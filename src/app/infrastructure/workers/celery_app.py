import logging
import os

from celery import Celery
from celery.signals import worker_process_init, worker_ready

from app.config.base import get_settings
from palitra import run as async_run

logger = logging.getLogger(__name__)

redis_url = os.getenv("REDIS_URL", "redis://localhost:16377/0")

celery_app = Celery("docalchemy")

# Register the task modules so the worker can dispatch any task name.
# The generic pack worker serves every provider queue; the provider URL is
# given per worker instance via PACK_ID / PROVIDER_URL environment variables.
import app.infrastructure.workers.pack_worker  # noqa: F401

# Acknowledge tasks only after they finish. With Celery's default (early ack,
# on receipt) a worker that is restarted or killed mid-task drops the task
# silently — the message is already gone from Redis, but the analysis_run row
# stays "running" forever (an orphan). Late ack keeps the message in Redis
# until the task returns, so a dead worker's task is redelivered instead of
# lost. See docs/specs note in this repo's commit history for the orphan bug.
#
# visibility_timeout must exceed the longest possible task runtime (docling on
# a 120-page PDF can run tens of minutes); if a worker is still grinding when
# it fires, Redis would prematurely redeliver. 6h is a safe ceiling here.
celery_app.conf.update(
    broker_url=redis_url,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,
    worker_prefetch_multiplier=1,
    broker_transport_options={"visibility_timeout": 6 * 60 * 60},
    visibility_timeout=6 * 60 * 60,
)


@worker_process_init.connect
def _configure_worker_logging(**_: object) -> None:
    """Apply the same SQLAlchemy logger settings used by the web process.

    The Litestar logging config (which sets ``propagate: False`` on the
    ``sqlalchemy.engine`` / ``sqlalchemy.pool`` loggers) only applies to the
    web process.  Inside the fork-pool worker those records propagate up to
    Celery's root logger, which re-emits them as WARNING — producing doubled,
    mis-levelled output.

    We reuse the same ``settings.log.SQLALCHEMY_LEVEL`` value so both
    processes share one source of truth.
    """
    settings = get_settings()
    level = settings.log.SQLALCHEMY_LEVEL

    for name in ("sqlalchemy.engine", "sqlalchemy.pool"):
        logger = logging.getLogger(name)
        logger.propagate = False
        logger.setLevel(level)


@worker_ready.connect
def _requeue_orphaned_runs_on_boot(**_: object) -> None:
    """Self-heal orphaned analysis runs when a worker starts.

    Fires once per worker instance (docling and opendataloader each boot their
    own process importing this module). Any run still "running" past the
    staleness cutoff is flipped back to "queued" and re-dispatched. A per-run
    Redis lock (NX) prevents the two instances from double-dispatching the same
    run when they boot together.

    Failures are logged and swallowed — a boot hook must never block worker
    startup.
    """
    from app.config.db import alchemy
    from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork
    from app.infrastructure.workers.requeue_stale_runs import requeue_stale_runs
    from app.domain.providers.registry import create_default_registry

    try:
        registry = create_default_registry()

        def _send(run_id, source_document_id, config, queue):
            task_name = f"run_analysis.pack.{queue.removeprefix('analysis.')}"
            celery_app.send_task(task_name, args=[str(run_id), str(source_document_id), config], queue=queue)

        async def _drain() -> list[str]:
            lock_client = None
            try:
                from redis.asyncio import Redis

                lock_client = Redis.from_url(redis_url)
                async with alchemy.get_session() as session:
                    uow = SqlAlchemyAnalysisUnitOfWork(session)
                    return await requeue_stale_runs(uow, _send, registry, lock_client=lock_client)
            finally:
                if lock_client is not None:
                    await lock_client.aclose()

        requeued = async_run(_drain())
        if requeued:
            logger.info("Boot janitor requeued %d orphaned run(s): %s", len(requeued), requeued)
    except Exception:
        logger.exception("Boot janitor failed; worker will continue normally")

"""Requeue orphaned analysis runs.

A run can be stranded in "running" with no live worker task behind it. The
classic cause (before late-ack) is an early-acking worker restarted or killed
mid-task: the Celery message is gone from Redis, but the DB row still reads
"running" forever.

This module re-dispatches such runs: it flips the row back to "queued",
resets started_at, and sends a fresh Celery task. Safe to run from the worker
boot hook (self-heal on restart) or as a one-off.

Scope is intentionally narrow: only "running" runs past the staleness cutoff
are touched. "queued"/"pending" runs are left alone — with late-ack enabled,
their message may still be live in Redis, and re-dispatching would duplicate
them. Redis's visibility_timeout already redelivers genuinely lost queued
tasks, so the janitor need not.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.domain.analysis.value_objects import AnalysisStatus

logger = logging.getLogger(__name__)

# A run "running" for longer than this with no progress is treated as orphaned.
# Generous: docling on a 120-page PDF legitimately runs tens of minutes.
STALE_RUNNING_SECONDS = 30 * 60


def _redis_lock_key(run_id: object) -> str:
    return f"requeue:run:{run_id}"


async def requeue_stale_runs(
    uow: AbstractAnalysisUnitOfWork,
    send_task,
    registry,
    *,
    lock_client=None,
    stale_running_seconds: int = STALE_RUNNING_SECONDS,
) -> list[str]:
    """Find "running" runs stuck past the cutoff and re-dispatch them.

    Args:
        uow: analysis unit of work (provides ``runs`` repo + commit).
        send_task: callable matching ``DispatchAnalysisRun._dispatch_task`` —
            ``(run_id, source_document_id, config, queue) -> None``.
        registry: ProviderRegistry, used to resolve each run's queue name.
        lock_client: optional redis client; when given, a per-run lock prevents
            the two worker instances (docling + opendataloader) from
            double-dispatching the same run on simultaneous boot. May be None
            for a single-process/CLI invocation.
        stale_running_seconds: runs "running" longer than this are requeued.

    Returns:
        The IDs of runs that were re-dispatched.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(seconds=stale_running_seconds)

    async with uow:
        active = await uow.runs.get_active_runs()

    requeued: list[str] = []
    for run in active:
        if run.status != AnalysisStatus.RUNNING:
            continue
        if run.started_at is not None and run.started_at > cutoff:
            continue  # genuinely in flight

        if lock_client is not None:
            acquired = await lock_client.set(_redis_lock_key(run.id), "1", nx=True, ex=300)
            if not acquired:
                continue  # another worker instance already picked it up

        definition = registry.get(run.provider_id)
        run.status = AnalysisStatus.QUEUED
        run.started_at = None
        run.finished_at = None
        async with uow:
            await uow.runs.update(run)
            await uow.commit()

        send_task(run.id, run.source_document_id, run.requested_config, definition.queue_name)
        requeued.append(str(run.id))
        logger.info("Requeued orphaned analysis run %s (provider=%s)", run.id, run.provider_id)

    return requeued

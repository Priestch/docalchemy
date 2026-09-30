"""The pack worker: the generic shape every pack provider will use.

Where the docling worker imports an engine adapter and an engine normalizer,
this one imports the pack adapter and the pack normalizer — engine knowledge
lives in the provider process, not here. The queue name and provider URL come
from the environment so the same file serves any pack:

    PROVIDER_URL=http://127.0.0.1:8099 PACK_ID=docling-pack \
        celery -A app.infrastructure.workers.pack_worker ...
"""

from __future__ import annotations

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from datetime import datetime, timezone
from pathlib import Path

from app.infrastructure.providers.pack.adapter import PackAdapter
from app.infrastructure.providers.pack.normalizer import pack_raw_to_render_document
from app.infrastructure.storage import StorageService
from app.infrastructure.workers.celery_app import celery_app
from palitra import run as async_run

logger = logging.getLogger(__name__)

PACK_ID = os.getenv("PACK_ID", "docling-pack")
QUEUE = os.getenv("PACK_QUEUE", f"analysis.{PACK_ID}")
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://127.0.0.1:8099")


@celery_app.task(bind=True, name=f"run_analysis.pack.{PACK_ID}", queue=QUEUE)
def run_analysis(self, run_id: str, source_document_id: str, config: dict) -> None:
    from app.config.db import alchemy
    from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork

    storage = StorageService(
        root_path=Path(os.getenv("STORAGE_ROOT_PATH", str(Path(__file__).parent.parent.parent.parent.parent / "storage")))
    )
    adapter = PackAdapter(storage=storage, provider_url=PROVIDER_URL, pack_id=PACK_ID)

    async def _run() -> None:
        async with alchemy.get_session() as session:
            uow = SqlAlchemyAnalysisUnitOfWork(session)
            run = await uow.runs.get(run_id)
            run.status = "running"
            run.started_at = datetime.now(tz=timezone.utc)
            await uow.runs.update(run)
            await uow.commit()

        from sqlalchemy import select
        from app.infrastructure.orm.source_document import SourceDocumentORM

        async with alchemy.get_session() as session:
            stmt = select(SourceDocumentORM.storage_key).where(SourceDocumentORM.id == source_document_id)
            result = await session.execute(stmt)
            storage_key = result.scalar_one()

        from app.domain.providers.contract import ProviderInput

        provider_input = ProviderInput(
            source_storage_key=storage_key,
            source_mime_type="application/pdf",
            config=config,
        )

        output = adapter.execute(provider_input)

        normalized = next(a for a in output.raw_artifacts if a.artifact_type == "normalized")
        normalized_data = json.loads(storage.get(normalized.storage_key))

        render_doc = pack_raw_to_render_document(
            normalized_data,
            {
                "pack_id": PACK_ID,
                "runtime_metadata": output.metadata,
                "normalized_at": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

        from app.application.use_cases.mark_analysis_run_succeeded import MarkAnalysisRunSucceeded

        async with alchemy.get_session() as session:
            uow = SqlAlchemyAnalysisUnitOfWork(session)
            use_case = MarkAnalysisRunSucceeded(uow=uow, storage=storage)
            await use_case.execute(
                run_id=run_id,
                raw_artifacts=output.raw_artifacts,
                render_document_data=render_doc.model_dump(),
                runtime_metadata=output.metadata,
            )

    try:
        async_run(_run())
    except Exception:
        logger.exception("Analysis failed for run %s", run_id)
        import traceback

        async def _mark_failed() -> None:
            async with alchemy.get_session() as session:
                uow = SqlAlchemyAnalysisUnitOfWork(session)
                from app.application.use_cases.mark_analysis_run_failed import MarkAnalysisRunFailed

                use_case = MarkAnalysisRunFailed(uow=uow)
                await use_case.execute(
                    run_id=run_id,
                    error_code="PROVIDER_ERROR",
                    error_message=traceback.format_exc()[:2000],
                )

        try:
            async_run(_mark_failed())
        except Exception:
            logger.exception("Failed to mark run as failed")

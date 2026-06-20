from __future__ import annotations

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from datetime import datetime, timezone
from pathlib import Path

from app.domain.providers.registry import create_default_registry
from app.infrastructure.providers.mineru.adapter import MinerUAdapter
from app.infrastructure.providers.mineru.normalizer import mineru_raw_to_render_document
from app.infrastructure.storage import StorageService
from palitra import run as async_run

from app.infrastructure.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_analysis_mineru", queue="analysis.mineru")
def run_analysis(self, run_id: str, source_document_id: str, config: dict) -> None:
    from app.config.db import alchemy
    from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork

    registry = create_default_registry()
    definition = registry.get("mineru")

    storage = StorageService(
        root_path=Path(os.getenv("STORAGE_ROOT_PATH", str(Path(__file__).parent.parent.parent.parent.parent / "storage")))
    )
    adapter = MinerUAdapter(storage=storage)

    async def _run() -> None:
        from sqlalchemy import select
        from app.infrastructure.orm.source_document import SourceDocumentORM

        async with alchemy.get_session() as session:
            uow = SqlAlchemyAnalysisUnitOfWork(session)
            run = await uow.runs.get(run_id)
            run.status = "running"
            run.started_at = datetime.now(tz=timezone.utc)
            await uow.runs.update(run)
            await uow.commit()

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

        raw_artifact = output.raw_artifacts[0]
        raw_data = json.loads(storage.get(raw_artifact.storage_key))

        render_doc = mineru_raw_to_render_document(
            raw_data,
            {
                "provider_id": "mineru",
                "provider_version": definition.version,
                "raw_artifact_storage_key": raw_artifact.storage_key,
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
        error_message = traceback.format_exc()[:2000]

        async def _mark_failed() -> None:
            async with alchemy.get_session() as session:
                uow = SqlAlchemyAnalysisUnitOfWork(session)
                from app.application.use_cases.mark_analysis_run_failed import MarkAnalysisRunFailed

                use_case = MarkAnalysisRunFailed(uow=uow)
                await use_case.execute(
                    run_id=run_id,
                    error_code="PROVIDER_ERROR",
                    error_message=error_message,
                )

        try:
            async_run(_mark_failed())
        except Exception:
            logger.exception("Failed to mark run as failed")

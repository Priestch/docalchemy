from __future__ import annotations

from uuid import UUID

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.domain.analysis.value_objects import AnalysisStatus
from app.domain.providers.registry import ProviderRegistry


class DispatchAnalysisRun:
    def __init__(
        self,
        uow: AbstractAnalysisUnitOfWork,
        provider_registry: ProviderRegistry,
    ) -> None:
        self._uow = uow
        self._registry = provider_registry

    async def execute(self, run_id: UUID) -> None:
        async with self._uow as uow:
            run = await uow.runs.get(run_id)
            run.status = AnalysisStatus.QUEUED
            await uow.runs.update(run)
            await uow.commit()

        definition = self._registry.get(run.provider_id)
        self._dispatch_task(run.id, run.source_document_id, run.requested_config, definition.queue_name)

    def _dispatch_task(self, run_id: UUID, source_document_id: UUID, config: dict, queue: str) -> None:
        from app.infrastructure.workers.celery_app import celery_app

        task_map = {
            "analysis.docling": "run_analysis",
            "analysis.opendataloader": "run_analysis_opendataloader",
            "analysis.mineru": "run_analysis_mineru",
            "analysis.surya": "run_analysis_surya",
        }
        task_name = task_map.get(queue, "run_analysis")
        celery_app.send_task(
            task_name,
            args=[str(run_id), str(source_document_id), config],
            queue=queue,
        )

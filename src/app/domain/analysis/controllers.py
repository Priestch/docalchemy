from __future__ import annotations

from uuid import UUID

from litestar import Controller, get, post
from litestar.di import Provide

from app.application.use_cases.create_analysis_run import CreateAnalysisRun
from app.application.use_cases.dispatch_analysis_run import DispatchAnalysisRun
from app.application.use_cases.get_render_document import GetRenderDocument
from app.domain.analysis.dependencies import (
    provide_analysis_uow,
    provide_create_analysis_run,
    provide_dispatch_analysis_run,
    provide_get_render_document,
    provide_provider_registry,
    provide_storage_service,
)
from app.domain.analysis.dtos import AnalysisArtifactDTO, AnalysisRunDTO, CreateAnalysisRunDTO
from app.domain.providers.registry import ProviderRegistry
from app.infrastructure.render_document import RenderDocument
from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork


class AnalysisController(Controller):
    path = "documents/{document_id:uuid}/analysis-runs"

    dependencies = {
        "analysis_uow": Provide(provide_analysis_uow),
        "provider_registry": Provide(provide_provider_registry),
        "create_run_use_case": Provide(provide_create_analysis_run),
        "dispatch_use_case": Provide(provide_dispatch_analysis_run),
    }

    @post()
    async def create_run(
        self,
        document_id: UUID,
        data: CreateAnalysisRunDTO,
        create_run_use_case: CreateAnalysisRun,
        dispatch_use_case: DispatchAnalysisRun,
    ) -> AnalysisRunDTO:
        dto = await create_run_use_case.execute(
            source_document_id=str(document_id),
            provider_id=data.provider_id,
            config=data.config,
        )
        try:
            await dispatch_use_case.execute(dto.id)
            dto.status = "queued"
        except Exception:
            pass
        return dto

    @get()
    async def list_runs(
        self,
        document_id: UUID,
        analysis_uow: SqlAlchemyAnalysisUnitOfWork,
    ) -> list[AnalysisRunDTO]:
        async with analysis_uow:
            runs = await analysis_uow.runs.get_by_document(document_id)
            result = []
            for run in runs:
                result.append(
                    AnalysisRunDTO(
                        id=run.id,
                        source_document_id=run.source_document_id,
                        provider_id=run.provider_id,
                        provider_version=run.provider_version,
                        status=run.status,
                        requested_config=run.requested_config,
                        runtime_metadata=run.runtime_metadata,
                        started_at=run.started_at,
                        finished_at=run.finished_at,
                        error_code=run.error_code,
                        error_message=run.error_message,
                        created_at=run.created_at,
                        updated_at=run.updated_at,
                    )
                )
        return result


class AnalysisRunController(Controller):
    path = "analysis-runs"

    dependencies = {
        "analysis_uow": Provide(provide_analysis_uow),
        "storage_service": Provide(provide_storage_service),
        "get_render_use_case": Provide(provide_get_render_document),
    }

    @get("/{run_id:uuid}")
    async def get_run(
        self,
        run_id: UUID,
        analysis_uow: SqlAlchemyAnalysisUnitOfWork,
    ) -> AnalysisRunDTO:
        async with analysis_uow:
            run = await analysis_uow.runs.get(run_id)
            artifacts = await analysis_uow.artifacts.get_by_run(run_id)

        return AnalysisRunDTO(
            id=run.id,
            source_document_id=run.source_document_id,
            provider_id=run.provider_id,
            provider_version=run.provider_version,
            status=run.status,
            requested_config=run.requested_config,
            runtime_metadata=run.runtime_metadata,
            started_at=run.started_at,
            finished_at=run.finished_at,
            error_code=run.error_code,
            error_message=run.error_message,
            artifacts=[AnalysisArtifactDTO(id=a.id, artifact_type=a.artifact_type, format=a.format) for a in artifacts],
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @get("/{run_id:uuid}/render")
    async def get_render(
        self,
        run_id: UUID,
        get_render_use_case: GetRenderDocument,
    ) -> RenderDocument:
        return await get_render_use_case.execute(run_id)

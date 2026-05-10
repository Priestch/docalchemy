from __future__ import annotations

from typing import Annotated
from uuid import UUID

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.params import Parameter

from app.application.use_cases.create_comparison_session import CreateComparisonSession
from app.application.use_cases.get_comparison_session import GetComparisonSession
from app.domain.analysis.dependencies import provide_analysis_uow, provide_storage_service
from app.domain.comparison.dependencies import (
    provide_comparison_uow,
    provide_create_comparison_session,
    provide_get_comparison_session,
)
from app.domain.comparison.dtos import ComparisonSessionDTO, ComparisonSessionDetailDTO, CreateComparisonSessionDTO
from app.domain.documents.dependencies import provide_documents_uow


class ComparisonController(Controller):
    path = "comparison-sessions"

    dependencies = {
        "comparison_uow": Provide(provide_comparison_uow),
        "analysis_uow": Provide(provide_analysis_uow),
        "documents_uow": Provide(provide_documents_uow),
        "storage_service": Provide(provide_storage_service),
        "create_session_use_case": Provide(provide_create_comparison_session),
        "get_session_use_case": Provide(provide_get_comparison_session),
    }

    @post()
    async def create(
        self,
        data: CreateComparisonSessionDTO,
        create_session_use_case: CreateComparisonSession,
    ) -> ComparisonSessionDTO:
        return await create_session_use_case.execute(
            source_document_id=str(data.source_document_id),
            analysis_run_ids=[str(rid) for rid in data.analysis_run_ids],
        )

    @get("/{session_id:uuid}")
    async def get(
        self,
        session_id: UUID,
        get_session_use_case: GetComparisonSession,
    ) -> ComparisonSessionDetailDTO:
        return await get_session_use_case.execute(session_id)

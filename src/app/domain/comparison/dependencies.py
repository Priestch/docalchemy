from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from app.application.use_cases.create_comparison_session import CreateComparisonSession
from app.application.use_cases.get_comparison_session import GetComparisonSession
from app.infrastructure.storage import StorageService
from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork, SqlAlchemyComparisonUnitOfWork, SqlAlchemyDocumentsUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_comparison_uow(db_session: AsyncSession) -> AsyncGenerator[SqlAlchemyComparisonUnitOfWork, None]:
    async with SqlAlchemyComparisonUnitOfWork(session=db_session) as uow:
        yield uow


def provide_create_comparison_session(
    comparison_uow: SqlAlchemyComparisonUnitOfWork,
    analysis_uow: SqlAlchemyAnalysisUnitOfWork,
) -> CreateComparisonSession:
    return CreateComparisonSession(
        comparison_uow=comparison_uow,
        analysis_uow=analysis_uow,
    )


def provide_get_comparison_session(
    comparison_uow: SqlAlchemyComparisonUnitOfWork,
    analysis_uow: SqlAlchemyAnalysisUnitOfWork,
    documents_uow: SqlAlchemyDocumentsUnitOfWork,
    storage_service: StorageService,
) -> GetComparisonSession:
    from app.infrastructure.repositories.source_document_repo import SqlAlchemySourceDocumentRepository

    docs_repo = SqlAlchemySourceDocumentRepository(documents_uow._session)

    return GetComparisonSession(
        comparison_uow=comparison_uow,
        analysis_uow=analysis_uow,
        documents_repo=docs_repo,
        storage=storage_service,
    )

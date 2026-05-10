from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.application.use_cases.create_analysis_run import CreateAnalysisRun
from app.application.use_cases.dispatch_analysis_run import DispatchAnalysisRun
from app.application.use_cases.get_render_document import GetRenderDocument
from app.domain.providers.registry import ProviderRegistry, create_default_registry
from app.infrastructure.storage import StorageService
from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_analysis_uow(db_session: AsyncSession) -> AsyncGenerator[SqlAlchemyAnalysisUnitOfWork, None]:
    async with SqlAlchemyAnalysisUnitOfWork(session=db_session) as uow:
        yield uow


def provide_provider_registry() -> ProviderRegistry:
    return create_default_registry()


def provide_storage_service() -> StorageService:
    import os

    root_path = (
        Path(os.getenv("STORAGE_ROOT_PATH"))
        if os.getenv("STORAGE_ROOT_PATH")
        else Path(__file__).parent.parent.parent.parent.parent / "storage"
    )
    return StorageService(root_path=root_path)


def provide_create_analysis_run(
    analysis_uow: SqlAlchemyAnalysisUnitOfWork,
    provider_registry: ProviderRegistry,
) -> CreateAnalysisRun:
    return CreateAnalysisRun(uow=analysis_uow, provider_registry=provider_registry)


def provide_dispatch_analysis_run(
    analysis_uow: SqlAlchemyAnalysisUnitOfWork,
    provider_registry: ProviderRegistry,
) -> DispatchAnalysisRun:
    return DispatchAnalysisRun(uow=analysis_uow, provider_registry=provider_registry)


def provide_get_render_document(
    analysis_uow: SqlAlchemyAnalysisUnitOfWork,
    storage_service: StorageService,
) -> GetRenderDocument:
    return GetRenderDocument(uow=analysis_uow, storage=storage_service)

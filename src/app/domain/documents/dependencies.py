from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING

from app.application.documents_uow import AbstractDocumentsUnitOfWork
from app.application.use_cases.upload_source_document import UploadSourceDocument
from app.domain.providers.registry import ProviderRegistry, create_default_registry
from app.infrastructure.storage import StorageService
from app.infrastructure.uow import SqlAlchemyDocumentsUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def provide_storage_service() -> StorageService:
    import os

    root_path = (
        Path(os.getenv("STORAGE_ROOT_PATH"))
        if os.getenv("STORAGE_ROOT_PATH")
        else Path(__file__).parent.parent.parent.parent.parent / "storage"
    )
    return StorageService(root_path=root_path)


async def provide_documents_uow(db_session: AsyncSession) -> AsyncGenerator[SqlAlchemyDocumentsUnitOfWork, None]:
    async with SqlAlchemyDocumentsUnitOfWork(session=db_session) as uow:
        yield uow


def provide_upload_source_document(
    documents_uow: SqlAlchemyDocumentsUnitOfWork,
    storage_service: StorageService,
) -> UploadSourceDocument:
    return UploadSourceDocument(uow=documents_uow, storage=storage_service)

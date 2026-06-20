from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.documents.entities import PageDimensions, SourceDocument
from app.domain.documents.repositories import AbstractSourceDocumentRepository
from app.infrastructure.orm.source_document import SourceDocumentORM


def _to_entity(orm: SourceDocumentORM) -> SourceDocument:
    dims = []
    for d in orm.page_dimensions or []:
        if isinstance(d, dict):
            dims.append(PageDimensions(**d))
    return SourceDocument(
        id=orm.id,
        name=orm.name,
        mime_type=orm.mime_type,
        size_bytes=orm.size_bytes,
        storage_key=orm.storage_key,
        checksum=orm.checksum,
        page_count=orm.page_count,
        page_dimensions=dims,
        uploaded_by=orm.uploaded_by,
        slug=orm.slug,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def _to_orm(entity: SourceDocument, orm: SourceDocumentORM | None = None) -> SourceDocumentORM:
    if orm is None:
        orm = SourceDocumentORM()
    orm.id = entity.id
    orm.name = entity.name
    orm.mime_type = entity.mime_type
    orm.size_bytes = entity.size_bytes
    orm.storage_key = entity.storage_key
    orm.checksum = entity.checksum
    orm.page_count = entity.page_count
    orm.page_dimensions = [d.model_dump() for d in entity.page_dimensions]
    orm.uploaded_by = entity.uploaded_by
    orm.slug = entity.slug
    return orm


class SqlAlchemySourceDocumentRepository(AbstractSourceDocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> SourceDocument:
        stmt = select(SourceDocumentORM).where(SourceDocumentORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()
        return _to_entity(orm)

    async def add(self, entity: SourceDocument) -> SourceDocument:
        orm = _to_orm(entity)
        self._session.add(orm)
        await self._session.flush()
        return _to_entity(orm)

    async def list(self, offset: int = 0, limit: int = 50) -> list[SourceDocument]:
        stmt = select(SourceDocumentORM).order_by(SourceDocumentORM.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def count(self) -> int:
        stmt = select(func.count()).select_from(SourceDocumentORM)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete(self, id: UUID) -> None:
        stmt = select(SourceDocumentORM).where(SourceDocumentORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()
        await self._session.delete(orm)

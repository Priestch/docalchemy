from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.analysis.entities import AnalysisRun
from app.domain.analysis.repositories import AbstractAnalysisRunRepository
from app.domain.analysis.value_objects import AnalysisStatus
from app.infrastructure.orm.analysis_run import AnalysisRunORM


def _to_entity(orm: AnalysisRunORM) -> AnalysisRun:
    return AnalysisRun(
        id=orm.id,
        source_document_id=orm.source_document_id,
        provider_id=orm.provider_id,
        provider_version=orm.provider_version,
        status=AnalysisStatus(orm.status),
        requested_config=orm.requested_config or {},
        runtime_metadata=orm.runtime_metadata,
        started_at=orm.started_at,
        finished_at=orm.finished_at,
        error_code=orm.error_code,
        error_message=orm.error_message,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


class SqlAlchemyAnalysisRunRepository(AbstractAnalysisRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> AnalysisRun:
        stmt = select(AnalysisRunORM).where(AnalysisRunORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()
        return _to_entity(orm)

    async def get_by_document(self, source_document_id: UUID) -> list[AnalysisRun]:
        stmt = (
            select(AnalysisRunORM)
            .where(AnalysisRunORM.source_document_id == source_document_id)
            .order_by(AnalysisRunORM.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def add(self, entity: AnalysisRun) -> AnalysisRun:
        orm = AnalysisRunORM(
            id=entity.id,
            source_document_id=entity.source_document_id,
            provider_id=entity.provider_id,
            provider_version=entity.provider_version,
            status=entity.status,
            requested_config=entity.requested_config,
            runtime_metadata=entity.runtime_metadata,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            error_code=entity.error_code,
            error_message=entity.error_message,
        )
        self._session.add(orm)
        await self._session.flush()
        return _to_entity(orm)

    async def update(self, entity: AnalysisRun) -> AnalysisRun:
        stmt = select(AnalysisRunORM).where(AnalysisRunORM.id == entity.id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()
        orm.status = entity.status
        orm.provider_version = entity.provider_version
        orm.runtime_metadata = entity.runtime_metadata
        orm.started_at = entity.started_at
        orm.finished_at = entity.finished_at
        orm.error_code = entity.error_code
        orm.error_message = entity.error_message
        await self._session.flush()
        return _to_entity(orm)

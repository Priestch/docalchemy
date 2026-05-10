from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.analysis.entities import AnalysisArtifact
from app.domain.analysis.repositories import AbstractAnalysisArtifactRepository
from app.domain.analysis.value_objects import ArtifactType
from app.infrastructure.orm.analysis_artifact import AnalysisArtifactORM


def _to_entity(orm: AnalysisArtifactORM) -> AnalysisArtifact:
    return AnalysisArtifact(
        id=orm.id,
        analysis_run_id=orm.analysis_run_id,
        artifact_type=ArtifactType(orm.artifact_type),
        format=orm.format,
        storage_key=orm.storage_key,
        created_at=orm.created_at,
    )


class SqlAlchemyAnalysisArtifactRepository(AbstractAnalysisArtifactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> AnalysisArtifact:
        stmt = select(AnalysisArtifactORM).where(AnalysisArtifactORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()
        return _to_entity(orm)

    async def get_by_run(self, analysis_run_id: UUID) -> list[AnalysisArtifact]:
        stmt = (
            select(AnalysisArtifactORM)
            .where(AnalysisArtifactORM.analysis_run_id == analysis_run_id)
            .order_by(AnalysisArtifactORM.created_at)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def add(self, entity: AnalysisArtifact) -> AnalysisArtifact:
        orm = AnalysisArtifactORM(
            id=entity.id,
            analysis_run_id=entity.analysis_run_id,
            artifact_type=entity.artifact_type,
            format=entity.format,
            storage_key=entity.storage_key,
        )
        self._session.add(orm)
        await self._session.flush()
        return _to_entity(orm)

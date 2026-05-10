from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.comparison.entities import ComparisonSession
from app.domain.comparison.repositories import AbstractComparisonSessionRepository
from app.infrastructure.orm.comparison_session import ComparisonSessionORM


class SqlAlchemyComparisonSessionRepository(AbstractComparisonSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: UUID) -> ComparisonSession:
        stmt = select(ComparisonSessionORM).where(ComparisonSessionORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one()
        run_ids = [run.id for run in orm.analysis_runs] if orm.analysis_runs else []
        return ComparisonSession(
            id=orm.id,
            source_document_id=orm.source_document_id,
            analysis_run_ids=run_ids,
            created_by=orm.created_by,
            created_at=orm.created_at,
        )

    async def add(self, entity: ComparisonSession) -> ComparisonSession:
        from app.infrastructure.orm.analysis_run import AnalysisRunORM

        run_stmt = select(AnalysisRunORM).where(AnalysisRunORM.id.in_(entity.analysis_run_ids))
        run_result = await self._session.execute(run_stmt)
        runs = list(run_result.scalars().all())

        orm = ComparisonSessionORM(
            id=entity.id,
            source_document_id=entity.source_document_id,
            created_by=entity.created_by,
            analysis_runs=runs,
        )
        self._session.add(orm)
        await self._session.flush()
        return ComparisonSession(
            id=orm.id,
            source_document_id=orm.source_document_id,
            analysis_run_ids=entity.analysis_run_ids,
            created_by=entity.created_by,
            created_at=orm.created_at,
        )

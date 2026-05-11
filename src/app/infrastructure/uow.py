from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.application.documents_uow import AbstractDocumentsUnitOfWork
from app.infrastructure.repositories import (
    SqlAlchemyAnalysisArtifactRepository,
    SqlAlchemyAnalysisRunRepository,
    SqlAlchemySourceDocumentRepository,
)


class SqlAlchemyDocumentsUnitOfWork(AbstractDocumentsUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.documents = SqlAlchemySourceDocumentRepository(session)

    async def __aenter__(self) -> SqlAlchemyDocumentsUnitOfWork:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class SqlAlchemyAnalysisUnitOfWork(AbstractAnalysisUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.runs = SqlAlchemyAnalysisRunRepository(session)
        self.artifacts = SqlAlchemyAnalysisArtifactRepository(session)

    async def __aenter__(self) -> SqlAlchemyAnalysisUnitOfWork:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

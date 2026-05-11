from __future__ import annotations

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.application.documents_uow import AbstractDocumentsUnitOfWork
from tests.fakes.fake_repositories import (
    FakeAnalysisArtifactRepository,
    FakeAnalysisRunRepository,
    FakeSourceDocumentRepository,
)


class FakeDocumentsUnitOfWork(AbstractDocumentsUnitOfWork):
    def __init__(self) -> None:
        self.documents = FakeSourceDocumentRepository()
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> FakeDocumentsUnitOfWork:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        self._rolled_back = True


class FakeAnalysisUnitOfWork(AbstractAnalysisUnitOfWork):
    def __init__(self) -> None:
        self.runs = FakeAnalysisRunRepository()
        self.artifacts = FakeAnalysisArtifactRepository()
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> FakeAnalysisUnitOfWork:
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        self._rolled_back = True

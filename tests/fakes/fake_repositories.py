from __future__ import annotations

from uuid import UUID, uuid4

from app.domain.analysis.entities import AnalysisArtifact, AnalysisRun
from app.domain.analysis.repositories import AbstractAnalysisArtifactRepository, AbstractAnalysisRunRepository
from app.domain.analysis.value_objects import AnalysisStatus
from app.domain.comparison.entities import ComparisonSession
from app.domain.comparison.repositories import AbstractComparisonSessionRepository
from app.domain.documents.entities import SourceDocument
from app.domain.documents.repositories import AbstractSourceDocumentRepository


class FakeSourceDocumentRepository(AbstractSourceDocumentRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, SourceDocument] = {}

    async def get(self, id: UUID) -> SourceDocument:
        if id not in self._store:
            msg = f"SourceDocument {id} not found"
            raise ValueError(msg)
        return self._store[id]

    async def add(self, entity: SourceDocument) -> SourceDocument:
        self._store[entity.id] = entity
        return entity

    async def list(self, offset: int = 0, limit: int = 50) -> list[SourceDocument]:
        items = sorted(self._store.values(), key=lambda d: d.created_at, reverse=True)
        return items[offset : offset + limit]

    async def count(self) -> int:
        return len(self._store)


class FakeAnalysisRunRepository(AbstractAnalysisRunRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AnalysisRun] = {}

    async def get(self, id: UUID) -> AnalysisRun:
        if id not in self._store:
            msg = f"AnalysisRun {id} not found"
            raise ValueError(msg)
        return self._store[id]

    async def get_by_document(self, source_document_id: UUID) -> list[AnalysisRun]:
        return [r for r in self._store.values() if r.source_document_id == source_document_id]

    async def add(self, entity: AnalysisRun) -> AnalysisRun:
        self._store[entity.id] = entity
        return entity

    async def update(self, entity: AnalysisRun) -> AnalysisRun:
        self._store[entity.id] = entity
        return entity


class FakeAnalysisArtifactRepository(AbstractAnalysisArtifactRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AnalysisArtifact] = {}

    async def get(self, id: UUID) -> AnalysisArtifact:
        if id not in self._store:
            msg = f"AnalysisArtifact {id} not found"
            raise ValueError(msg)
        return self._store[id]

    async def get_by_run(self, analysis_run_id: UUID) -> list[AnalysisArtifact]:
        return [a for a in self._store.values() if a.analysis_run_id == analysis_run_id]

    async def add(self, entity: AnalysisArtifact) -> AnalysisArtifact:
        self._store[entity.id] = entity
        return entity


class FakeComparisonSessionRepository(AbstractComparisonSessionRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, ComparisonSession] = {}

    async def get(self, id: UUID) -> ComparisonSession:
        if id not in self._store:
            msg = f"ComparisonSession {id} not found"
            raise ValueError(msg)
        return self._store[id]

    async def add(self, entity: ComparisonSession) -> ComparisonSession:
        self._store[entity.id] = entity
        return entity

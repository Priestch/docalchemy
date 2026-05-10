from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.analysis.entities import AnalysisArtifact, AnalysisRun


class AbstractAnalysisRunRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID) -> AnalysisRun: ...

    @abstractmethod
    async def get_by_document(self, source_document_id: UUID) -> list[AnalysisRun]: ...

    @abstractmethod
    async def add(self, entity: AnalysisRun) -> AnalysisRun: ...

    @abstractmethod
    async def update(self, entity: AnalysisRun) -> AnalysisRun: ...


class AbstractAnalysisArtifactRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID) -> AnalysisArtifact: ...

    @abstractmethod
    async def get_by_run(self, analysis_run_id: UUID) -> list[AnalysisArtifact]: ...

    @abstractmethod
    async def add(self, entity: AnalysisArtifact) -> AnalysisArtifact: ...

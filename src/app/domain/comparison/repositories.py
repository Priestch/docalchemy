from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.comparison.entities import ComparisonSession


class AbstractComparisonSessionRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID) -> ComparisonSession: ...

    @abstractmethod
    async def add(self, entity: ComparisonSession) -> ComparisonSession: ...

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.documents.entities import SourceDocument


class AbstractSourceDocumentRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID) -> SourceDocument: ...

    @abstractmethod
    async def get_by_checksum(self, checksum: str) -> SourceDocument | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> SourceDocument | None: ...

    @abstractmethod
    async def add(self, entity: SourceDocument) -> SourceDocument: ...

    @abstractmethod
    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        q: str | None = None,
        provider: str | None = None,
    ) -> list[SourceDocument]: ...

    @abstractmethod
    async def count(self, q: str | None = None, provider: str | None = None) -> int: ...

    @abstractmethod
    async def delete(self, id: UUID) -> None: ...

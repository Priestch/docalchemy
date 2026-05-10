from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractUnitOfWork(ABC):
    @abstractmethod
    async def __aenter__(self) -> AbstractUnitOfWork: ...

    @abstractmethod
    async def __aexit__(self, exc_type: type | None, exc_val: BaseException | None, exc_tb: object) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

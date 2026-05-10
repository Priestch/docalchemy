from __future__ import annotations

from app.application.unit_of_work import AbstractUnitOfWork
from app.domain.comparison.repositories import AbstractComparisonSessionRepository


class AbstractComparisonUnitOfWork(AbstractUnitOfWork):
    sessions: AbstractComparisonSessionRepository

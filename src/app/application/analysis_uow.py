from __future__ import annotations

from app.application.unit_of_work import AbstractUnitOfWork
from app.domain.analysis.repositories import AbstractAnalysisArtifactRepository, AbstractAnalysisRunRepository


class AbstractAnalysisUnitOfWork(AbstractUnitOfWork):
    runs: AbstractAnalysisRunRepository
    artifacts: AbstractAnalysisArtifactRepository

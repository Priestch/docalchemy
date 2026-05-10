from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.application.comparison_uow import AbstractComparisonUnitOfWork
from app.domain.analysis.value_objects import AnalysisStatus
from app.domain.comparison.dtos import ComparisonSessionDTO
from app.domain.comparison.entities import ComparisonSession


class CreateComparisonSession:
    def __init__(
        self,
        comparison_uow: AbstractComparisonUnitOfWork,
        analysis_uow: AbstractAnalysisUnitOfWork,
    ) -> None:
        self._comparison_uow = comparison_uow
        self._analysis_uow = analysis_uow

    async def execute(
        self,
        source_document_id: str,
        analysis_run_ids: list[str],
    ) -> ComparisonSessionDTO:
        if len(analysis_run_ids) < 2:
            msg = "At least 2 runs required for comparison"
            raise ValueError(msg)

        runs = []
        for run_id in analysis_run_ids:
            async with self._analysis_uow as uow:
                run = await uow.runs.get(run_id)
            runs.append(run)

        doc_ids = {str(r.source_document_id) for r in runs}
        if len(doc_ids) > 1 or str(doc_ids.pop()) != str(source_document_id):
            msg = "All runs must belong to the same source document"
            raise ValueError(msg)

        for run in runs:
            if run.status != AnalysisStatus.SUCCESS:
                msg = f"Run {run.id} has status {run.status}, expected success"
                raise ValueError(msg)

        now = datetime.now(tz=timezone.utc)
        entity = ComparisonSession(
            id=uuid4(),
            source_document_id=source_document_id,
            analysis_run_ids=analysis_run_ids,
            created_at=now,
        )

        async with self._comparison_uow as uow:
            await uow.sessions.add(entity)
            await uow.commit()

        return ComparisonSessionDTO(
            id=entity.id,
            source_document_id=entity.source_document_id,
            analysis_run_ids=entity.analysis_run_ids,
            created_at=entity.created_at,
        )

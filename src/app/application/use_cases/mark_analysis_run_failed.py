from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.application.analysis_uow import AbstractAnalysisUnitOfWork


class MarkAnalysisRunFailed:
    def __init__(self, uow: AbstractAnalysisUnitOfWork) -> None:
        self._uow = uow

    async def execute(
        self,
        run_id: UUID,
        error_code: str,
        error_message: str,
    ) -> None:
        now = datetime.now(tz=timezone.utc)

        async with self._uow as uow:
            run = await uow.runs.get(run_id)
            run.status = "failed"
            run.finished_at = now
            run.error_code = error_code
            run.error_message = error_message
            await uow.runs.update(run)
            await uow.commit()

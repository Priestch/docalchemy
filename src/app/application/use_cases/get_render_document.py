from __future__ import annotations

from uuid import UUID

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.domain.analysis.value_objects import ArtifactType, AnalysisStatus
from app.infrastructure.render_document import RenderDocument
from app.infrastructure.storage import StorageService


class GetRenderDocument:
    def __init__(
        self,
        uow: AbstractAnalysisUnitOfWork,
        storage: StorageService,
    ) -> None:
        self._uow = uow
        self._storage = storage

    async def execute(self, run_id: UUID) -> RenderDocument:
        async with self._uow as uow:
            run = await uow.runs.get(run_id)

            if run.status != AnalysisStatus.SUCCESS:
                msg = f"Run {run_id} has status {run.status}, expected success"
                raise ValueError(msg)

            artifacts = await uow.artifacts.get_by_run(run_id)
            render_artifact = next(
                (a for a in artifacts if a.artifact_type == ArtifactType.RENDER_DOCUMENT),
                None,
            )

            if render_artifact is None:
                msg = f"No render document artifact found for run {run_id}"
                raise ValueError(msg)

        data = self._storage.get(render_artifact.storage_key)
        import json

        return RenderDocument.model_validate(json.loads(data))

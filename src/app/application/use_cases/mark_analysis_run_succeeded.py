from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.domain.analysis.entities import AnalysisArtifact
from app.domain.analysis.value_objects import ArtifactType
from app.domain.providers.contract import RawArtifact
from app.infrastructure.storage import StorageService


class MarkAnalysisRunSucceeded:
    def __init__(
        self,
        uow: AbstractAnalysisUnitOfWork,
        storage: StorageService,
    ) -> None:
        self._uow = uow
        self._storage = storage

    async def execute(
        self,
        run_id: UUID,
        raw_artifacts: list[RawArtifact],
        render_document_data: dict,
        runtime_metadata: dict | None = None,
    ) -> None:
        now = datetime.now(tz=timezone.utc)

        render_storage_key = self._storage.save(render_document_data, suffix=".json")

        async with self._uow as uow:
            run = await uow.runs.get(run_id)
            run.status = "success"
            run.finished_at = now
            run.runtime_metadata = runtime_metadata or {}

            for artifact in raw_artifacts:
                entity = AnalysisArtifact(
                    id=uuid4(),
                    analysis_run_id=run_id,
                    artifact_type=ArtifactType(artifact.artifact_type),
                    format=artifact.format,
                    storage_key=artifact.storage_key,
                    created_at=now,
                )
                await uow.artifacts.add(entity)

            render_artifact = AnalysisArtifact(
                id=uuid4(),
                analysis_run_id=run_id,
                artifact_type=ArtifactType.RENDER_DOCUMENT,
                format="json",
                storage_key=render_storage_key,
                created_at=now,
            )
            await uow.artifacts.add(render_artifact)
            await uow.runs.update(run)
            await uow.commit()

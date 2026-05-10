from __future__ import annotations

import json
from uuid import UUID

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.application.comparison_uow import AbstractComparisonUnitOfWork
from app.domain.analysis.value_objects import ArtifactType
from app.domain.comparison.dtos import ComparisonRunDTO, ComparisonSessionDetailDTO
from app.domain.documents.repositories import AbstractSourceDocumentRepository
from app.infrastructure.storage import StorageService


class GetComparisonSession:
    def __init__(
        self,
        comparison_uow: AbstractComparisonUnitOfWork,
        analysis_uow: AbstractAnalysisUnitOfWork,
        documents_repo: AbstractSourceDocumentRepository,
        storage: StorageService,
    ) -> None:
        self._comparison_uow = comparison_uow
        self._analysis_uow = analysis_uow
        self._documents_repo = documents_repo
        self._storage = storage

    async def execute(self, session_id: UUID) -> ComparisonSessionDetailDTO:
        async with self._comparison_uow as uow:
            session = await uow.sessions.get(session_id)

        source_doc = await self._documents_repo.get(session.source_document_id)

        from app.domain.documents.dtos import SourceDocumentDTO

        source_dto = SourceDocumentDTO(
            id=source_doc.id,
            name=source_doc.name,
            mime_type=source_doc.mime_type,
            size_bytes=source_doc.size_bytes,
            storage_key=source_doc.storage_key,
            checksum=source_doc.checksum,
            page_count=source_doc.page_count,
            page_dimensions=source_doc.page_dimensions,
            slug=source_doc.slug,
            created_at=source_doc.created_at,
            updated_at=source_doc.updated_at,
        )

        runs = []
        for run_id in session.analysis_run_ids:
            async with self._analysis_uow as uow:
                run = await uow.runs.get(run_id)
                artifacts = await uow.artifacts.get_by_run(run_id)

            render_artifact = next(
                (a for a in artifacts if a.artifact_type == ArtifactType.RENDER_DOCUMENT),
                None,
            )

            render_data = None
            if render_artifact:
                raw = self._storage.get(render_artifact.storage_key)
                render_data = json.loads(raw)

            runs.append(
                ComparisonRunDTO(
                    run_id=run.id,
                    provider_id=run.provider_id,
                    render_document=render_data,
                )
            )

        return ComparisonSessionDetailDTO(
            id=session.id,
            source_document=source_dto,
            runs=runs,
            created_at=session.created_at,
        )

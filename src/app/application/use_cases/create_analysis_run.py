from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.analysis_uow import AbstractAnalysisUnitOfWork
from app.domain.analysis.dtos import AnalysisRunDTO
from app.domain.analysis.entities import AnalysisRun
from app.domain.analysis.value_objects import AnalysisStatus
from app.domain.providers.registry import ProviderRegistry


class CreateAnalysisRun:
    def __init__(
        self,
        uow: AbstractAnalysisUnitOfWork,
        provider_registry: ProviderRegistry,
    ) -> None:
        self._uow = uow
        self._registry = provider_registry

    async def execute(
        self,
        source_document_id: str,
        provider_id: str,
        config: dict | None = None,
    ) -> AnalysisRunDTO:
        if not self._registry.has(provider_id):
            msg = f"Unknown provider: {provider_id}"
            raise ValueError(msg)

        definition = self._registry.get(provider_id)
        now = datetime.now(tz=timezone.utc)

        entity = AnalysisRun(
            id=uuid4(),
            source_document_id=source_document_id,
            provider_id=provider_id,
            provider_version=definition.version,
            status=AnalysisStatus.PENDING,
            requested_config=config or {},
            created_at=now,
            updated_at=now,
        )

        async with self._uow as uow:
            await uow.runs.add(entity)
            await uow.commit()

        return AnalysisRunDTO(
            id=entity.id,
            source_document_id=entity.source_document_id,
            provider_id=entity.provider_id,
            provider_version=entity.provider_version,
            status=entity.status,
            requested_config=entity.requested_config,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

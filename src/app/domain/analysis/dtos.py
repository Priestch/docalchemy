from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.analysis.value_objects import AnalysisStatus, ArtifactType


class AnalysisRunDTO(BaseModel):
    id: UUID
    source_document_id: UUID
    provider_id: str
    provider_version: str = ""
    status: AnalysisStatus
    requested_config: dict = Field(default_factory=dict)
    runtime_metadata: dict | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    artifacts: list[AnalysisArtifactDTO] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CreateAnalysisRunDTO(BaseModel):
    provider_id: str
    config: dict = Field(default_factory=dict)


class AnalysisArtifactDTO(BaseModel):
    id: UUID
    artifact_type: ArtifactType
    format: str

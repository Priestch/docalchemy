from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.analysis.dtos import AnalysisRunDTO
from app.domain.documents.dtos import SourceDocumentDTO


class ComparisonSessionDTO(BaseModel):
    id: UUID
    source_document_id: UUID
    analysis_run_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime


class CreateComparisonSessionDTO(BaseModel):
    source_document_id: UUID
    analysis_run_ids: list[UUID]


class ComparisonSessionDetailDTO(BaseModel):
    id: UUID
    source_document: SourceDocumentDTO
    runs: list[ComparisonRunDTO]
    created_at: datetime


class ComparisonRunDTO(BaseModel):
    run_id: UUID
    provider_id: str
    render_document: dict | None = None

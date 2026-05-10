from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ComparisonSession(BaseModel):
    id: UUID
    source_document_id: UUID
    analysis_run_ids: list[UUID] = Field(default_factory=list)
    created_by: str | None = None
    created_at: datetime

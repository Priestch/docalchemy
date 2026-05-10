from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.documents.entities import PageDimensions


class SourceDocumentDTO(BaseModel):
    id: UUID
    name: str
    mime_type: str
    size_bytes: int
    storage_key: str
    checksum: str
    page_count: int = 0
    page_dimensions: list[PageDimensions] = Field(default_factory=list)
    uploaded_by: str | None = None
    slug: str = ""
    created_at: datetime
    updated_at: datetime


class SourceDocumentListDTO(BaseModel):
    items: list[SourceDocumentDTO]
    total: int
    offset: int
    limit: int

from __future__ import annotations

from advanced_alchemy.base import SlugKey, UUIDAuditBase
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class SourceDocumentORM(UUIDAuditBase, SlugKey):
    __tablename__ = "source_document"

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(length=100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Not unique on purpose: every upload creates its own row, while storage
    # stays content-addressed — rows for the same bytes share one file.
    storage_key: Mapped[str] = mapped_column(String(length=64), nullable=False)
    checksum: Mapped[str] = mapped_column(String(length=32), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_dimensions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    uploaded_by: Mapped[str | None] = mapped_column(String(length=255), nullable=True)

from __future__ import annotations

from datetime import datetime

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class AnalysisRunORM(UUIDAuditBase):
    __tablename__ = "analysis_run"

    source_document_id: Mapped[str] = mapped_column(ForeignKey("source_document.id"), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(length=50), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(length=20), nullable=False, default="")
    status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        default="pending",
    )
    requested_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(length=50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

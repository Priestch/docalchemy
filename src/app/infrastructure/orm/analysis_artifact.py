from __future__ import annotations

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class AnalysisArtifactORM(UUIDAuditBase):
    __tablename__ = "analysis_artifact"

    analysis_run_id: Mapped[str] = mapped_column(ForeignKey("analysis_run.id", ondelete="CASCADE"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(length=30), nullable=False)
    format: Mapped[str] = mapped_column(String(length=10), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(length=64), nullable=False)

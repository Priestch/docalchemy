from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import Column, ForeignKey, String, Table, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.orm.analysis_run import AnalysisRunORM

comparison_session_runs = Table(
    "comparison_session_runs",
    UUIDAuditBase.metadata,
    Column("comparison_session_id", Uuid, ForeignKey("comparison_session.id"), primary_key=True),
    Column("analysis_run_id", Uuid, ForeignKey("analysis_run.id"), primary_key=True),
)


class ComparisonSessionORM(UUIDAuditBase):
    __tablename__ = "comparison_session"

    source_document_id: Mapped[str] = mapped_column(ForeignKey("source_document.id"), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(length=255), nullable=True)

    analysis_runs: Mapped[list["AnalysisRunORM"]] = relationship(
        secondary=comparison_session_runs,
        lazy="selectin",
    )

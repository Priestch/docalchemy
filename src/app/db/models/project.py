from __future__ import annotations

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column


class Project(UUIDAuditBase):
    __tablename__ = "project"
    __table_args__ = {"comment": "Project for uploaded file."}
    __pii_columns__ = {"name", "status"}

    name: Mapped[str] = mapped_column(nullable=False, default="")
    store_key: Mapped[str] = mapped_column(nullable=False)
    owner: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[int] = mapped_column(default=0)

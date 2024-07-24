from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    # from .oauth_account import UserOauthAccount
    # from .team_member import TeamMember
    # from .user_role import UserRole
    pass


class Project(UUIDAuditBase):
    __tablename__ = "project"
    __table_args__ = {"comment": "Project for uploaded file."}
    __pii_columns__ = {"name", "status"}

    name: Mapped[str] = mapped_column(nullable=False, default="")
    store_key: Mapped[str] = mapped_column(nullable=False)
    owner: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[int] = mapped_column(default=0)

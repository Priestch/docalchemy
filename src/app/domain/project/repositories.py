from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from app.db.models import Project

__all__ = ("ProjectRepository",)


class ProjectRepository(SQLAlchemyAsyncRepository[Project]):
    """Project Repository."""

    model_type = Project

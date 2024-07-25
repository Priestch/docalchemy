from __future__ import annotations

from advanced_alchemy.repository import SQLAlchemyAsyncRepository, SQLAlchemySyncRepository

from app.db.models import Project

__all__ = ["ProjectRepository", "ProjectSyncRepository"]


class ProjectRepository(SQLAlchemyAsyncRepository[Project]):
    """Project Repository."""

    model_type = Project


class ProjectSyncRepository(SQLAlchemySyncRepository[Project]):
    """Sync Project Repository."""

    model_type = Project

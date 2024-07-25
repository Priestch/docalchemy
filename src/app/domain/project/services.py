from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, SQLAlchemySyncRepositoryService

from app.db.models import Project

from .repositories import ProjectRepository, ProjectSyncRepository


class ProjectService(SQLAlchemyAsyncRepositoryService[Project]):
    """Project Service."""

    repository_type = ProjectRepository

    async def create_from_file(self, filedata: dict) -> Project:
        data = {
            "name": filedata.get("name"),
            "store_key": filedata.get("store_key"),
            "owner": filedata.get("owner"),
            "status": 0,
        }
        return await super().create(data, auto_commit=True)


class ProjectSyncService(SQLAlchemySyncRepositoryService[Project]):
    """Project Service."""

    repository_type = ProjectSyncRepository

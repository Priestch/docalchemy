from structlog import get_logger

from app.config.app import alchemy_sync

__all__ = ["stroke_furnace"]

from app.domain.project.services import ProjectSyncService
from app.file_storage import storage
from app.furnace import FurnaceService
from app.task_queue import celery_app

logger = get_logger()


@celery_app.task
def stroke_furnace(project_id: str) -> None:
    with alchemy_sync.get_session() as session:
        project_service = ProjectSyncService(session)
        project = project_service.get(project_id)

        logger.info(f"Stroke furnace for {project.name}...")

        project.status = 10
        project_service.update(project, auto_commit=True)

    service = FurnaceService(storage)
    file_path = storage.root_path.joinpath(project.store_key)
    service.start(file_path)

    with alchemy_sync.get_session() as session:
        project_service = ProjectSyncService(session)
        project = project_service.get(project_id)

        project.status = 100
        project_service.update(project, auto_commit=True)

    logger.info(f"Finished furnace for {project.name}.")


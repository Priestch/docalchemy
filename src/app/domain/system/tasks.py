import asyncio

from saq.types import Context
from structlog import get_logger

from app.config.app import alchemy_sync

__all__ = ["stroke_furnace", "system_upkeep"]

from app.domain.project.services import ProjectSyncService
from app.task_queue import celery_app

logger = get_logger()


async def system_upkeep(_: Context) -> None:
    await logger.ainfo("Performing system upkeep operations.")
    await logger.ainfo("Simulating a long running operation.  Sleeping for 60 seconds.")
    await asyncio.sleep(60)
    await logger.ainfo("Simulating an even long running operation.  Sleeping for 120 seconds.")
    await asyncio.sleep(120)
    await logger.ainfo("Long running process complete.")
    await logger.ainfo("Performing system upkeep operations.")


@celery_app.task
def stroke_furnace(project_id: str) -> None:
    with alchemy_sync.get_session() as session:
        project = ProjectSyncService(session).get(project_id)
        logger.info(f"Stroke furnace for {project.id}...")


import asyncio
import importlib.util
import logging
import sys
from pathlib import Path

from celery import Celery

from app.config.db import alchemy
from app.domain import FileService, FileStatus
from app.infrastructure.storage import storage

app = Celery("app", broker="redis://redis:6379/0")

logger = logging.getLogger(__file__)


def import_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


async def handle_analyse_done(file_meta: dict) -> None:
    async with alchemy.get_session() as session:
        async with FileService.new(session) as service:
            file = await service.get_one(id=file_meta["id"])
            await service.update({"status": FileStatus.SUCCESS}, file.id, auto_commit=True)


@app.task
def analyse_document(file_meta: dict, lib: str, **kwargs) -> None:
    logger.debug(f"Analyse {file_meta} by {lib}")
    file_path = storage.resolve(file_meta["hashed_filename"])
    logger.debug(f"Analyse {file_path} by {lib} configured with {kwargs}")
    analyser_module = import_from_path(f"{lib}_analyser", Path(__file__).parent / (lib + ".py"))
    analyser = analyser_module.Analyser.configure(**kwargs)
    result_filename = analyser.analyse(file_path)

    file_meta = file_meta | {"result": result_filename}
    asyncio.run(handle_analyse_done(file_meta))

from __future__ import annotations

import logging
from enum import UNIQUE, IntEnum, verify
from typing import TYPE_CHECKING

from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, is_dict, is_msgspec_model, is_pydantic_model
from litestar.events import listener

from app.celery_app import app
from app.db.models import File
from app.domain.file.repositories import FileRepository

logger = logging.getLogger(__file__)


if TYPE_CHECKING:
    from advanced_alchemy.service import ModelDictT


@verify(UNIQUE)
class FileStatus(
    IntEnum,
):
    PENDING = 1
    SUCCESS = 2


@listener("file_uploaded")
async def analyse_file(file_meta: dict, analyser: str) -> None:
    app.send_task("app.analyser.tasks.analyse_document", args=[file_meta, analyser])


@verify(UNIQUE)
class AnalyserType(IntEnum):
    DOCLING = 1


class FileService(SQLAlchemyAsyncRepositoryService[File]):
    repository_type = FileRepository

    async def to_model(self, data: ModelDictT[File], operation: str | None = None) -> File:
        if (is_msgspec_model(data) or is_pydantic_model(data)) and operation == "create" and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if (is_msgspec_model(data) or is_pydantic_model(data)) and operation == "update" and data.slug is None:  # type: ignore[union-attr]
            data.slug = await self.repository.get_available_slug(data.name)  # type: ignore[union-attr]
        if is_dict(data) and "slug" not in data and operation == "create":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        if is_dict(data) and "slug" not in data and "name" in data and operation == "update":
            data["slug"] = await self.repository.get_available_slug(data["name"])
        return await super().to_model(data, operation)

from pathlib import Path
from typing import Annotated

from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app.celery_app import app
from app.infrastructure.storage import storage


class FileController(Controller):
    path = "files"

    @post()
    async def upload(self, data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]) -> object:
        filename = storage.save(data.file.read(), Path(data.filename).suffix.lower())
        app.send_task("analyser.tasks.analyse_document", args=[filename, "docling"])
        return {"filename": data.filename}

    @get()
    async def get_files(self) -> object:
        return "files"

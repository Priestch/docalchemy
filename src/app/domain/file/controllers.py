from pathlib import Path
from typing import Annotated, Sequence
from urllib.request import Request
from uuid import UUID

from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.response import File as FileResponse

from app.db.models import File
from app.domain.file.dependencies import provide_files_service
from app.domain.file.services import AnalyserType, FileService, FileStatus
from app.infrastructure.storage import storage


class FileController(Controller):
    path = "files"

    dependencies = {"files_service": Provide(provide_files_service)}
    signature_namespace = {"files_service": FileService}

    @post()
    async def upload(
        self,
        files_service: FileService,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
        request: Request,
    ) -> File:
        filename = storage.save(data.file.read(), Path(data.filename).suffix.lower())
        data = {
            "name": data.filename,
            "status": FileStatus.PENDING,
            "hashed_filename": filename,
        }
        file = await files_service.create(data, auto_commit=True)

        request.app.emit(
            "file_uploaded",
            file_meta={"id": file.id, "hashed_filename": file.hashed_filename},
            analyser=AnalyserType.DOCLING.name.lower(),
        )

        return file

    @get()
    async def get_files(self, files_service: FileService) -> Sequence[File]:
        return await files_service.list()

    @get("/{file_id:uuid/upload")
    async def get_file(
        self,
        file_id: Annotated[
            UUID,
            Parameter(
                title="User ID",
                description="The user to delete.",
            ),
        ],
        files_service: FileService,
    ) -> FileResponse:
        file = await files_service.get_one(id=file_id)
        file_path = storage.resolve(file.hashed_filename)
        return FileResponse(path=file_path, filename=file.name)

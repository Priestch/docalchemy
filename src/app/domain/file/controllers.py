from typing import Annotated

from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body


class FileController(Controller):
    path = "files"

    @post()
    async def upload(self, data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]) -> object:
        print("file", data)
        return {"filename": data.filename}

    @get()
    async def get_files(self) -> object:
        return "files"

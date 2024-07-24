from __future__ import annotations

import hashlib
import os.path
from typing import Annotated, TYPE_CHECKING

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body

from app.domain.project.dependencies import provide_project_service
from app.domain.project.schemas import Project
from app.domain.project.services import ProjectService
from app.file_storage import storage
from app.domain.project.urls import PROJECT_LIST


if TYPE_CHECKING:
    from litestar.connection import Request
    from advanced_alchemy.service.pagination import OffsetPagination


class ProjectController(Controller):
    """Project Controller."""

    path = PROJECT_LIST
    dependencies = {"project_service": Provide(provide_project_service)}
    signature_namespace = {"ProjectService": ProjectService}

    @get(
        operation_id="ProjectList",
        name="project:list",
        status_code=HTTP_200_OK,
    )
    async def index(
            self,
            request: Request,
            current_user: str,
            project_service: ProjectService
    ) -> OffsetPagination[Project]:
        """Serve site root."""
        request.logger.info("-"*80, current_user)
        projects = await project_service.list()
        data = project_service.to_schema(projects, schema_type=Project)
        data.items.append(data.items[0])
        return data

    @post(
        operation_id="CreateProject",
        name="project:create",
        status_code=HTTP_200_OK,
    )
    async def create(
            self,
            request: Request,
            current_user: str,
            data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
            project_service: ProjectService
    ) -> Project:
        request.logger.info("create project", current_user)
        content = await data.read()
        md5 = hashlib.md5(content).hexdigest()
        _, ext = os.path.splitext(data.filename)
        filename = f"{md5}{ext}"
        data = {"name": data.filename, "store_key": filename, "owner": current_user}
        project = await project_service.create_from_file(data)
        storage.put(filename, content)

        return project_service.to_schema(project, schema_type=Project)

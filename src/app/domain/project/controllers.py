from __future__ import annotations

import hashlib
import os.path
from typing import TYPE_CHECKING, Annotated

from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK

from app.domain.project.dependencies import provide_project_service
from app.domain.project.schemas import Project
from app.domain.project.services import ProjectService
from app.domain.project.urls import PROJECT_LIST
from app.domain.system import tasks
from app.file_storage import storage

if TYPE_CHECKING:
    from advanced_alchemy.service.pagination import OffsetPagination
    from litestar import Request


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
            project_service: ProjectService,
    ) -> OffsetPagination[Project]:
        """Serve site root."""
        current_user = request.get_session_id()

        request.logger.debug(f"get project lists for {current_user}")

        projects = await project_service.list(owner=current_user)
        return project_service.to_schema(projects, schema_type=Project)

    @post(
        operation_id="CreateProject",
        name="project:create",
        status_code=HTTP_200_OK,
    )
    async def create(
            self,
            request: Request,
            data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
            project_service: ProjectService,
    ) -> Project:
        current_user = request.get_session_id()

        request.logger.debug(f"create project for {current_user}: {data.filename}")

        content = await data.read()
        md5 = hashlib.md5(content).hexdigest()
        _, ext = os.path.splitext(data.filename)
        filename = f"{md5}{ext.lower()}"
        data = {"name": data.filename, "store_key": filename, "owner": current_user}
        project = await project_service.create_from_file(data)

        request.logger.debug(f"save {filename}:{len(content)} to storage")
        storage.put(filename, content)

        request.logger.debug(f"send {project.id!s} to queue. {type(project.id.hex)}")
        job = tasks.stroke_furnace.apply_async((str(project.id), ))


        return project_service.to_schema(project, schema_type=Project)

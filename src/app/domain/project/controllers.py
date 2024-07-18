from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK

from app.domain.project.urls import PROJECT_LIST
from app.domain.urls import API_VERSION


class ProjectController(Controller):
    """Project Controller."""

    include_in_schema = False
    opt = {"exclude_from_auth": True}
    path = PROJECT_LIST

    @get(
        operation_id="ProjectList",
        name="project:list",
        status_code=HTTP_200_OK,
    )
    async def index(self, path: str | None = None) -> str:
        """Serve site root."""
        return "Hello Projects"

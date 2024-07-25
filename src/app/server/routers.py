"""Application Modules."""
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.router import Router

from app.domain.project.controllers import ProjectController
from app.domain.urls import API_VERSION

# from app.domain.accounts.controllers import AccessController, UserController, UserRoleController
# from app.domain.system.controllers import SystemController
# from app.domain.tags.controllers import TagController
# from app.domain.teams.controllers import TeamController, TeamMemberController
from app.domain.web.controllers import WebController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler

api_handlers = [ProjectController]
route_handlers: list[ControllerRouterHandler] = [
    # AccessController,
    # UserController,
    # TeamController,
    # UserRoleController,
    #  TeamInvitationController,
    # TeamMemberController,
    # TagController,
    # SystemController,
    Router(path=API_VERSION, route_handlers=api_handlers),
    WebController,
]

from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Router, get

from app.domain.file.controllers import FileController
from app.domain.web.controllers import WebController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


api_router = Router(path="/api", route_handlers=[FileController])

route_handlers: list[ControllerRouterHandler] = [
    WebController,
    api_router,
]

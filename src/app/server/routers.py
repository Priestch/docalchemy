from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import get

from app.domain.web.controllers import WebController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


@get("/")
async def hello_world() -> dict[str, str]:
    """Handler function that returns a greeting dictionary."""
    return {"hello": "world"}


route_handlers: list[ControllerRouterHandler] = [
    WebController,
]

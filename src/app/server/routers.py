"""Route assembly: the SPA shell plus the platform API, mounted from the gateway.

All document/analysis/provider surface lives in docalchemy-gateway; this app
bridges its DI (the plugin's db_session, an env-configured storage root) and
contributes only the web shell. Scenario features (comparison, chat, ...) add
their routers here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.web.controllers import WebController
from docalchemy_gateway.platform import StorageService, build_api_router

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


async def provide_platform_session(db_session: AsyncSession) -> AsyncSession:
    """The gateway handlers name their dependency `session`; the app's plugin
    provides `db_session`. This bridges the two without a second engine."""
    yield db_session


def provide_storage_service() -> StorageService:
    root = os.getenv("STORAGE_ROOT_PATH", str(Path(__file__).parents[3] / "storage"))
    return StorageService(root_path=Path(root))


api_router = build_api_router(
    Provide(provide_platform_session),
    Provide(provide_storage_service, sync_to_thread=False),
)

route_handlers: list[ControllerRouterHandler] = [
    WebController,
    api_router,
]

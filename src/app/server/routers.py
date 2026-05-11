from __future__ import annotations

from typing import TYPE_CHECKING

from litestar import Router

from app.domain.analysis.controllers import AnalysisController, AnalysisRunController
from app.domain.documents.controllers import DocumentController
from app.domain.file.controllers import FileController
from app.domain.providers.controllers import ProviderController
from app.domain.web.controllers import WebController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler


api_router = Router(
    path="/api",
    route_handlers=[
        DocumentController,
        AnalysisController,
        AnalysisRunController,
        ProviderController,
        FileController,
    ],
)

route_handlers: list[ControllerRouterHandler] = [
    WebController,
    api_router,
]

# pylint: disable=[invalid-name,import-outside-toplevel]
# SPDX-FileCopyrightText: 2023-present Cody Fincher <cody.fincher@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import TYPE_CHECKING

from app.server import plugins

if TYPE_CHECKING:
    from litestar import Litestar


def create_app() -> Litestar:
    """Create ASGI application."""

    from litestar import Litestar
    from litestar.contrib.jinja import JinjaTemplateEngine
    from litestar.template.config import TemplateConfig

    from app.config.app import settings
    from app.config import app as config
    from app.server import routers

    return Litestar(
        cors_config=config.cors,
        debug=settings.app.DEBUG,
        route_handlers=routers.route_handlers,
        template_config=TemplateConfig(
            directory=settings.vite.TEMPLATE_DIR,
            engine=JinjaTemplateEngine,
        ),
        plugins=[
            plugins.alchemy,
            plugins.vite,
        ],
        request_max_body_size=100_000_000,
    )


app = create_app()

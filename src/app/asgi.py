# pylint: disable=[invalid-name,import-outside-toplevel]
# SPDX-FileCopyrightText: 2023-present Cody Fincher <cody.fincher@gmail.com>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations

import logging
from os import urandom
from typing import TYPE_CHECKING

from litestar import MediaType, Request, Response
from litestar.exceptions import NotFoundException
from litestar.logging import LoggingConfig
from litestar.middleware.session.client_side import CookieBackendConfig
from litestar.middleware.session.server_side import ServerSideSessionConfig

if TYPE_CHECKING:
    from litestar import Litestar
    from litestar.connection import Request


# we initialize to config with a 16 byte key, i.e. 128 a bit key.
# in real world usage we should inject the secret from the environment
session_config = CookieBackendConfig(secret=urandom(16))  # type: ignore[arg-type]

logging_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.INFO), "handlers": ["console"]},
    formatters={
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
)


def validation_exception_handler(request: Request, exc: NotFoundException) -> Response:
    return Response(
        media_type=MediaType.TEXT,
        content=f"validation error: {exc.detail}",
        status_code=400,
    )


def create_app() -> Litestar:
    """Create ASGI application."""

    from litestar import Litestar

    from app.config import app as config
    from app.config.base import get_settings

    # from app.domain.accounts import signals as account_signals
    # from app.domain.accounts.guards import auth
    # from app.domain.teams import signals as team_signals
    from app.lib.dependencies import create_collection_dependencies

    # from app.server import openapi, plugins, routers
    from app.server import plugins, routers

    dependencies = {}
    dependencies.update(create_collection_dependencies())
    settings = get_settings()

    return Litestar(
        cors_config=config.cors,
        # dependencies=dependencies,
        debug=settings.app.DEBUG,
        # openapi_config=openapi.config,
        route_handlers=routers.route_handlers,
        plugins=[
            plugins.app_config,
            plugins.structlog,
            plugins.alchemy,
            plugins.vite,
            plugins.granian,
        ],
        # on_app_init=[auth.on_app_init],
        # listeners=[account_signals.user_created_event_handler, team_signals.team_created_event_handler],
        middleware=[ServerSideSessionConfig().middleware],
        logging_config=logging_config,
        # exception_handlers={
        #     NotFoundException: validation_exception_handler,
        # },
    )


app = create_app()

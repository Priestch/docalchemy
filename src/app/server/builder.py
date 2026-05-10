# pylint: disable=[invalid-name,import-outside-toplevel]
from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.config.response_cache import ResponseCacheConfig, default_cache_key_builder
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar import Request
    from litestar.config.app import AppConfig


class ApplicationConfigurator(InitPluginProtocol):
    """Application configuration plugin."""

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        from app.config import get_settings

        settings = get_settings()
        app_config.response_cache_config = ResponseCacheConfig(
            key_builder=self._cache_key_builder,
        )
        app_config.signature_namespace.update({})

        try:
            from litestar.stores.redis import RedisStore
            from litestar.stores.registry import StoreRegistry

            redis = settings.redis.get_client()
            app_slug = settings.app.slug

            def redis_store_factory(name: str) -> RedisStore:
                return RedisStore(redis, namespace=f"{app_slug}:{name}")

            app_config.stores = StoreRegistry(default_factory=redis_store_factory)
            app_config.on_shutdown.append(redis.aclose)
        except Exception:
            pass

        return app_config

    def _cache_key_builder(self, request: Request) -> str:
        return f"docalchemy:{default_cache_key_builder(request)}"

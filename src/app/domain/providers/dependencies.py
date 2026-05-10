from __future__ import annotations

from app.domain.providers.registry import ProviderRegistry, create_default_registry


def provide_provider_registry() -> ProviderRegistry:
    return create_default_registry()

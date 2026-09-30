from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.providers.contract import ProviderCapabilities


@dataclass
class ProviderDefinition:
    provider_id: str
    display_name: str
    version: str
    capabilities: ProviderCapabilities
    supported_mime_types: list[str] = field(default_factory=lambda: ["application/pdf"])
    config_schema: dict = field(default_factory=dict)
    queue_name: str = ""
    timeout_seconds: int = 300
    # Recommended page limit for a single run on this provider. None means no
    # limit (the provider scales fine). Used to warn the user before triggering
    # a run on a large document that would take a very long time.
    max_pages: int | None = None
    endpoint: str | None = None


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderDefinition] = {}

    def register(self, definition: ProviderDefinition) -> None:
        self._providers[definition.provider_id] = definition

    def get(self, provider_id: str) -> ProviderDefinition:
        if provider_id not in self._providers:
            msg = f"Unknown provider: {provider_id}"
            raise ValueError(msg)
        return self._providers[provider_id]

    def list_all(self) -> list[ProviderDefinition]:
        return list(self._providers.values())

    def has(self, provider_id: str) -> bool:
        return provider_id in self._providers


def create_default_registry() -> ProviderRegistry:
    from app.domain.providers.definitions import (
        DOCLING_DEFINITION,
        FRANKENOCR_DEFINITION,
        MINERU_DEFINITION,
        OPENDATALOADER_DEFINITION,
    )

    registry = ProviderRegistry()
    registry.register(DOCLING_DEFINITION)
    registry.register(OPENDATALOADER_DEFINITION)
    registry.register(MINERU_DEFINITION)
    registry.register(FRANKENOCR_DEFINITION)
    return registry

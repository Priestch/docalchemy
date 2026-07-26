from __future__ import annotations

from litestar import Controller, get

from app.domain.providers.dependencies import provide_provider_registry
from app.domain.providers.registry import ProviderRegistry


class ProviderController(Controller):
    path = "providers"

    dependencies = {"provider_registry": provide_provider_registry}

    @get()
    async def list_providers(self, provider_registry: ProviderRegistry) -> list[dict]:
        return [
            {
                "provider_id": d.provider_id,
                "display_name": d.display_name,
                "version": d.version,
                "capabilities": {
                    "has_ocr": d.capabilities.has_ocr,
                    "has_table_extraction": d.capabilities.has_table_extraction,
                    "has_reading_order": d.capabilities.has_reading_order,
                    "has_formula": d.capabilities.has_formula,
                    "has_image_description": d.capabilities.has_image_description,
                },
                "supported_mime_types": d.supported_mime_types,
                "max_pages": d.max_pages,
            }
            for d in provider_registry.list_all()
        ]

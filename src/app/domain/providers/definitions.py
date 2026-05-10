from app.domain.providers.contract import ProviderCapabilities
from app.domain.providers.registry import ProviderDefinition

DOCLING_DEFINITION = ProviderDefinition(
    provider_id="docling",
    display_name="Docling",
    version="2.x",
    capabilities=ProviderCapabilities(
        has_ocr=False,
        has_table_extraction=True,
        has_reading_order=True,
        has_formula=False,
        has_image_description=False,
    ),
    supported_mime_types=["application/pdf"],
    config_schema={},
    queue_name="analysis.docling",
    timeout_seconds=300,
)

OPENDATALOADER_DEFINITION = ProviderDefinition(
    provider_id="opendataloader",
    display_name="OpenDataLoader PDF",
    version="2.x",
    capabilities=ProviderCapabilities(
        has_ocr=True,
        has_table_extraction=True,
        has_reading_order=True,
        has_formula=True,
        has_image_description=True,
    ),
    supported_mime_types=["application/pdf"],
    config_schema={
        "type": "object",
        "properties": {
            "hybrid": {"type": "string", "enum": ["off", "docling-fast"]},
        },
    },
    queue_name="analysis.opendataloader",
    timeout_seconds=600,
)

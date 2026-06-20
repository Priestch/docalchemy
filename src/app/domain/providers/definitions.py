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

MINERU_DEFINITION = ProviderDefinition(
    provider_id="mineru",
    display_name="MinerU",
    version="0.x",
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
            "method": {"type": "string", "enum": ["auto", "ocr", "txt"], "default": "auto"},
            "lang": {"type": "string"},
        },
    },
    queue_name="analysis.mineru",
    timeout_seconds=600,
)

SURYA_DEFINITION = ProviderDefinition(
    provider_id="surya",
    display_name="Surya OCR",
    version="0.x",
    capabilities=ProviderCapabilities(
        has_ocr=True,
        has_table_extraction=True,
        has_reading_order=True,
        has_formula=True,
        has_image_description=False,
    ),
    supported_mime_types=["application/pdf"],
    config_schema={
        "type": "object",
        "properties": {
            "langs": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["en"],
            },
        },
    },
    queue_name="analysis.surya",
    timeout_seconds=600,
)

from __future__ import annotations

from pathlib import Path

from app.domain.providers.contract import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderInput,
    ProviderOutput,
    RawArtifact,
)
from app.infrastructure.storage import StorageService


class DoclingAdapter(ProviderAdapter):
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    @property
    def provider_id(self) -> str:
        return "docling"

    @property
    def provider_version(self) -> str:
        return "2.x"

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            has_ocr=False,
            has_table_extraction=True,
            has_reading_order=True,
            has_formula=False,
            has_image_description=False,
        )

    def execute(self, input: ProviderInput) -> ProviderOutput:
        from docling.document_converter import DocumentConverter

        source_path = self._storage.resolve(input.source_storage_key)
        converter = DocumentConverter()
        result = converter.convert(source_path)
        doc_dict = result.document.export_to_dict()

        storage_key = self._storage.save(doc_dict, suffix=".json")

        return ProviderOutput(
            raw_artifacts=[
                RawArtifact(
                    artifact_type="raw_json",
                    storage_key=storage_key,
                    format="json",
                )
            ],
            metadata={"pages_processed": len(result.pages) if hasattr(result, "pages") else 0},
        )

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.domain.providers.contract import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderInput,
    ProviderOutput,
    RawArtifact,
)
from app.infrastructure.storage import StorageService


class OpenDataLoaderAdapter(ProviderAdapter):
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    @property
    def provider_id(self) -> str:
        return "opendataloader"

    @property
    def provider_version(self) -> str:
        return "2.x"

    @property
    def supported_mime_types(self) -> list[str]:
        return ["application/pdf"]

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            has_ocr=True,
            has_table_extraction=True,
            has_reading_order=True,
            has_formula=True,
            has_image_description=True,
        )

    def execute(self, input: ProviderInput) -> ProviderOutput:
        import opendataloader_pdf

        source_path = self._storage.resolve(input.source_storage_key)

        with tempfile.TemporaryDirectory() as tmp_dir:
            config = input.config or {}
            hybrid = config.get("hybrid", None)

            kwargs: dict = {
                "input_path": [str(source_path)],
                "output_dir": tmp_dir,
                "format": "json",
            }
            if hybrid:
                kwargs["hybrid"] = hybrid

            opendataloader_pdf.convert(**kwargs)

            output_files = list(Path(tmp_dir).glob("*.json"))
            if not output_files:
                msg = "OpenDataLoader produced no output files"
                raise RuntimeError(msg)

            raw_artifacts = []
            for output_file in output_files:
                with open(output_file) as f:
                    data = json.load(f)

                storage_key = self._storage.save(data, suffix=".json")
                raw_artifacts.append(
                    RawArtifact(
                        artifact_type="raw_json",
                        storage_key=storage_key,
                        format="json",
                    )
                )

        return ProviderOutput(
            raw_artifacts=raw_artifacts,
            metadata={"pages_processed": len(raw_artifacts)},
        )

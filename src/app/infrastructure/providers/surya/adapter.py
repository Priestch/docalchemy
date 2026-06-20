from __future__ import annotations

import tempfile
from pathlib import Path

from app.domain.providers.contract import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderError,
    ProviderInput,
    ProviderOutput,
    RawArtifact,
)
from app.infrastructure.storage import StorageService


class SuryaAdapter(ProviderAdapter):
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    @property
    def provider_id(self) -> str:
        return "surya"

    @property
    def provider_version(self) -> str:
        return "0.x"

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
            has_image_description=False,
        )

    def execute(self, input: ProviderInput) -> ProviderOutput:
        source_path = self._storage.resolve(input.source_storage_key)
        config = input.config or {}
        langs = config.get("langs", ["en"])
        if isinstance(langs, str):
            langs = [langs]

        result = self._run_surya(source_path, langs=langs)

        storage_key = self._storage.save(result, suffix=".json")

        return ProviderOutput(
            raw_artifacts=[
                RawArtifact(
                    artifact_type="raw_json",
                    storage_key=storage_key,
                    format="json",
                )
            ],
            metadata={"pages_processed": len(result) if isinstance(result, list) else 1},
        )

    def _run_surya(self, pdf_path: Path, langs: list[str]) -> list[dict]:
        return self._run_via_cli(pdf_path)

    def _run_via_cli(self, pdf_path: Path) -> list[dict]:
        import json
        import shutil
        import subprocess

        if not shutil.which("surya_ocr"):
            raise ProviderError(
                error_code="SURYA_CLI_MISSING",
                error_message=(
                    "surya_ocr CLI not found. "
                    "Install with: pip install surya-ocr"
                ),
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            cmd = ["surya_ocr", str(pdf_path), "--output_dir", tmp_dir]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                raise ProviderError(
                    error_code="SURYA_CLI_ERROR",
                    error_message=f"surya_ocr failed: {result.stderr[:500]}",
                )

            results_file = Path(tmp_dir) / "results.json"
            if not results_file.exists():
                found = list(Path(tmp_dir).rglob("results.json"))
                if found:
                    results_file = found[0]
                else:
                    raise ProviderError(
                        error_code="SURYA_NO_OUTPUT",
                        error_message="Surya CLI produced no results.json",
                    )

            with open(results_file) as f:
                data = json.load(f)

            # surya CLI returns {filename: [page_results, ...]}
            pages = []
            if isinstance(data, dict):
                for name, page_list in data.items():
                    for page in page_list:
                        page["_file"] = name
                        pages.append(page)
            else:
                pages = data if isinstance(data, list) else [data]
            return pages


def _serialize_block(block) -> dict:
    if hasattr(block, "__dict__"):
        return block.__dict__
    if isinstance(block, dict):
        return block
    return {}


def _serialize_text_line(tl) -> dict:
    if hasattr(tl, "__dict__"):
        return tl.__dict__
    if isinstance(tl, dict):
        return tl
    return {}

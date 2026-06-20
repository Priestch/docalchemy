from __future__ import annotations

import os
import subprocess
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


class MinerUAdapter(ProviderAdapter):
    def __init__(self, storage: StorageService) -> None:
        self._storage = storage

    @property
    def provider_id(self) -> str:
        return "mineru"

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
            has_formula=False,
            has_image_description=False,
        )

    def execute(self, input: ProviderInput) -> ProviderOutput:
        source_path = self._storage.resolve(input.source_storage_key)
        config = input.config or {}
        method = config.get("method", "auto")

        raw_objects = self._parse_pdf(source_path, method=method)

        raw_artifacts = []
        for obj in raw_objects:
            storage_key = self._storage.save(obj["data"], suffix=obj["suffix"])
            raw_artifacts.append(
                RawArtifact(
                    artifact_type=obj["artifact_type"],
                    storage_key=storage_key,
                    format=obj["format"],
                )
            )

        return ProviderOutput(
            raw_artifacts=raw_artifacts,
            metadata={"pages_processed": len(raw_objects)},
        )

    def _parse_pdf(self, pdf_path: Path, method: str = "auto") -> list[dict]:
        return self._parse_via_mineru_cli(pdf_path, method=method)

    def _parse_via_mineru_cli(self, pdf_path: Path, method: str = "auto") -> list[dict]:
        import shutil

        if not shutil.which("mineru"):
            raise ProviderError(
                error_code="MINERU_CLI_MISSING",
                error_message=(
                    "mineru CLI not found. "
                    "Install with: pip install mineru[core]"
                ),
            )

        with tempfile.TemporaryDirectory() as tmp_dir:
            cmd = [
                "mineru",
                "-p", str(pdf_path),
                "-o", tmp_dir,
                "-b", "pipeline",
                "-m", method,
                "-f", "False",
                "-t", "False",
            ]

            env = os.environ.copy()
            env.pop("HTTP_PROXY", None)
            env.pop("HTTPS_PROXY", None)
            env.pop("http_proxy", None)
            env.pop("https_proxy", None)
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
            if proc.returncode != 0:
                combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
                tail = combined.strip().split("\n")[-20:]
                raise ProviderError(
                    error_code="MINERU_CLI_ERROR",
                    error_message=f"mineru CLI failed:\n" + "\n".join(tail),
                )

            results = []
            json_files = sorted(
                [f for f in Path(tmp_dir).rglob("*.json")],
                key=lambda p: 0 if "_middle" in p.stem else 1,
            )
            for f in json_files:
                results.append({
                    "data": f.read_bytes(),
                    "suffix": ".json",
                    "artifact_type": "raw_json",
                    "format": "json",
                })
            md_file = next(Path(tmp_dir).rglob("*.md"), None)
            if md_file:
                results.append({
                    "data": md_file.read_bytes(),
                    "suffix": ".md",
                    "artifact_type": "raw_markdown",
                    "format": "md",
                })

            if not results:
                raise ProviderError(
                    error_code="MINERU_NO_OUTPUT",
                    error_message="mineru CLI produced no output files",
                )

            return results

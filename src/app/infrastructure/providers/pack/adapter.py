"""The provider-pack adapter: their ProviderAdapter interface over the
DocAlchemy job protocol.

Everything engine-shaped lives in a separate provider process speaking the
pack protocol; this adapter is the bridge the worker uses — materialize the
source from storage, run one job (submit, wait, result), and upload what the
provider wrote back into storage as raw artifacts. Two artifacts carry
particular meaning downstream:

- artifact_type "raw_json": the engine's own lossless export (audit,
  re-normalization insurance);
- artifact_type "normalized": the contract's normalized document, which the
  pack normalizer turns into a RenderDocument without ever touching the
  engine.
"""

from __future__ import annotations

import time
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import msgspec
from docalchemy_contract import Artifact, JobResult

from app.domain.providers.contract import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderError,
    ProviderInput,
    ProviderOutput,
    RawArtifact,
)
from app.infrastructure.storage import StorageService

_MIME_TO_FORMAT = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/html": "html",
}


class RemotePackAdapter(ProviderAdapter):
    """Speaks the pack job protocol to one provider process."""

    def __init__(self, storage: StorageService, *, provider_url: str, pack_id: str) -> None:
        self._storage = storage
        self._url = provider_url.rstrip("/")
        self._pack_id = pack_id
        self._manifest: dict | None = None

    @property
    def provider_id(self) -> str:
        return self._pack_id

    @property
    def provider_version(self) -> str:
        return str(self.manifest().get("version", "unknown"))

    @property
    def supported_mime_types(self) -> list[str]:
        formats = self.manifest().get("capabilities", {}).get("input_formats", [])
        mime_by_format = {v: k for k, v in _MIME_TO_FORMAT.items()}
        return sorted({mime_by_format[f] for f in formats if f in mime_by_format})

    @property
    def capabilities(self) -> ProviderCapabilities:
        elements = self.manifest().get("capabilities", {}).get("elements", {})
        return ProviderCapabilities(
            has_ocr=bool(self.manifest().get("capabilities", {}).get("ocr", {}).get("available")),
            has_table_extraction=elements.get("table", "none") != "none",
            has_reading_order=elements.get("heading", "none") != "none",
            has_formula=elements.get("formula", "none") != "none",
            has_image_description=False,
        )

    def manifest(self) -> dict:
        if self._manifest is None:
            response = httpx.get(f"{self._url}/manifest", timeout=10.0)
            response.raise_for_status()
            self._manifest = response.json()
        return self._manifest

    def execute(self, input: ProviderInput) -> ProviderOutput:
        source_path = self._storage.resolve(input.source_storage_key)
        if not source_path.exists():
            raise ProviderError("INPUT_NOT_FOUND", f"source not in storage: {input.source_storage_key}")

        input_format = _MIME_TO_FORMAT.get(input.source_mime_type, source_path.suffix.lstrip(".").lower())
        if not input.config:
            input.config = {}

        with TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp) / "artifacts"
            artifacts_dir.mkdir()
            accepted = httpx.post(
                f"{self._url}/jobs",
                json={
                    "input_uri": str(source_path),
                    "input_format": input_format,
                    "options": input.config,
                    "artifacts_dir": str(artifacts_dir),
                },
                timeout=30.0,
            )
            if accepted.status_code >= 300:
                # 201 is the protocol's success: Litestar's POST default.
                raise ProviderError("SUBMIT_FAILED", f"pack rejected the job: {accepted.text[:200]}")
            job_id = accepted.json()["job_id"]

            result = self._wait_for_result(job_id)
            if result.status != "succeeded":
                error = result.error
                raise ProviderError(
                    "PROVIDER_ERROR",
                    f"{error.code if error else 'unknown'}: {error.message if error else 'no detail'}",
                )

            raw_artifacts = self._upload(result.document, result.artifacts, artifacts_dir)
            engine = result.provenance.engine
            return ProviderOutput(
                raw_artifacts=raw_artifacts,
                metadata={
                    "pack_provider": self._pack_id,
                    "engine": {"name": engine.name, "version": engine.version} if engine else None,
                    "job_id": result.job_id,
                    "duration_ms": result.duration_ms,
                    "fidelity": result.fidelity,
                },
            )

    def _wait_for_result(self, job_id: str, timeout: float = 900.0) -> JobResult:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = httpx.get(f"{self._url}/jobs/{job_id}/result", timeout=30.0)
            if response.status_code == 200:
                return msgspec.json.decode(response.content, type=JobResult)
            if response.status_code == 404:
                raise ProviderError("JOB_LOST", f"pack lost job {job_id}")
            time.sleep(0.5)
        raise ProviderError("TIMEOUT", f"pack job {job_id} did not finish within {timeout}s")

    def _upload(self, document, artifacts: list[Artifact], artifacts_dir: Path) -> list[RawArtifact]:
        """Store the normalized document, the raw export, and every file the
        provider wrote; uris are names relative to the job's artifacts dir."""
        uploaded: list[RawArtifact] = []

        normalized = msgspec.json.encode(document)
        uploaded.append(
            RawArtifact(
                artifact_type="normalized",
                storage_key=self._storage.save(normalized, suffix=".json"),
                format="json",
            )
        )

        for artifact in artifacts:
            local = artifacts_dir / artifact.uri
            if not local.is_file():
                continue
            suffix = local.suffix or ".bin"
            if artifact.kind == "raw_json":
                uploaded.append(
                    RawArtifact(
                        artifact_type="raw_json",
                        storage_key=self._storage.save(local.read_bytes(), suffix=suffix),
                        format="json",
                    )
                )
            else:
                uploaded.append(
                    RawArtifact(
                        artifact_type=artifact.kind,
                        storage_key=self._storage.save(local.read_bytes(), suffix=suffix),
                        format=suffix.lstrip("."),
                    )
                )
        return uploaded

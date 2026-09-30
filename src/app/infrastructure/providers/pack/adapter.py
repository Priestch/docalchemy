"""The provider-pack adapter: their ProviderAdapter interface over a Host.

Everything engine-shaped lives in a separate provider process speaking the
pack protocol. This adapter builds a connect-mode Host from the provider's
own manifest (Host.from_endpoint) — so submit, SSE progress streaming, error
taxonomy, and contract gating all come from the SDK instead of a hand-rolled
HTTP client — and bridges storage: materialize the source, run one job,
upload what the provider wrote back as raw artifacts. Two artifact types
carry particular meaning downstream:

- artifact_type "raw_json": the engine's own lossless export (audit,
  re-normalization insurance);
- artifact_type "normalized": the contract's normalized document, which the
  pack normalizer turns into a RenderDocument without ever touching the
  engine.
"""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import msgspec
from docalchemy.contract import Artifact, JobResult
from docalchemy.host import Host, JobFailed, ProviderStartError

from app.domain.providers.contract import (
    ProviderAdapter,
    ProviderCapabilities,
    ProviderError,
    ProviderInput,
    ProviderOutput,
    RawArtifact,
)
from app.infrastructure.storage import StorageService

logger = logging.getLogger(__name__)

_MIME_TO_FORMAT = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/html": "html",
}


class PackAdapter(ProviderAdapter):
    """One pack behind one Host, in connect mode: the host never owns the
    provider process (docker or a service supervisor does) but keeps the full
    protocol semantics — progress streaming, error classes, contract checks."""

    def __init__(self, storage: StorageService, *, provider_url: str, pack_id: str) -> None:
        self._storage = storage
        self._pack_id = pack_id
        self._host = Host.from_endpoint(provider_url)
        self._manifest = self._host.providers()[0].manifest

    @property
    def provider_id(self) -> str:
        return self._pack_id

    @property
    def provider_version(self) -> str:
        return self._manifest.version

    @property
    def supported_mime_types(self) -> list[str]:
        formats = self._manifest.capabilities.input_formats
        mime_by_format = {v: k for k, v in _MIME_TO_FORMAT.items()}
        return sorted({mime_by_format[f] for f in formats if f in mime_by_format})

    @property
    def capabilities(self) -> ProviderCapabilities:
        caps = self._manifest.capabilities
        return ProviderCapabilities(
            has_ocr=bool(caps.ocr.available),
            has_table_extraction=caps.elements.get("table", "none") != "none",
            has_reading_order=caps.reading_order != "none",
            has_formula=caps.elements.get("formula", "none") != "none",
            has_image_description=False,
        )

    def execute(self, input: ProviderInput) -> ProviderOutput:
        source_path = self._storage.resolve(input.source_storage_key)
        if not source_path.exists():
            raise ProviderError("INPUT_NOT_FOUND", f"source not in storage: {input.source_storage_key}")

        input_format = _MIME_TO_FORMAT.get(input.source_mime_type, source_path.suffix.lstrip(".").lower())
        options = dict(input.config or {})

        with TemporaryDirectory() as tmp:
            artifacts_dir = Path(tmp) / "artifacts"
            artifacts_dir.mkdir()

            def on_progress(progress) -> None:
                # The pack's SSE progress, streamed live through the Host.
                # Surfaced in the worker log now; wiring it into the run's
                # progress reporting is the next integration step.
                logger.info("pack %s progress: %s", self._pack_id, progress.stage)

            try:
                result = self._host.parse(
                    self._manifest.name,
                    source_path,
                    options=options,
                    artifacts_dir=artifacts_dir,
                    on_progress=on_progress,
                )
            except JobFailed as exc:
                raise ProviderError(exc.code.value.upper(), f"{self._pack_id}: {exc.detail}") from exc
            except ProviderStartError as exc:
                raise ProviderError("PROVIDER_UNAVAILABLE", str(exc)) from exc

            return self._upload(result, artifacts_dir)

    def _upload(self, result: JobResult, artifacts_dir: Path) -> ProviderOutput:
        uploaded: list[RawArtifact] = [
            RawArtifact(
                artifact_type="normalized",
                storage_key=self._storage.save(msgspec.json.encode(result.document), suffix=".json"),
                format="json",
            )
        ]
        for artifact in result.artifacts:
            local = artifacts_dir / artifact.uri
            if not local.is_file():
                continue
            suffix = local.suffix or ".bin"
            artifact_type = "raw_json" if artifact.kind == "raw_json" else artifact.kind
            uploaded.append(
                RawArtifact(
                    artifact_type=artifact_type,
                    storage_key=self._storage.save(local.read_bytes(), suffix=suffix),
                    format=suffix.lstrip("."),
                )
            )
        engine = result.provenance.engine
        return ProviderOutput(
            raw_artifacts=uploaded,
            metadata={
                "pack_provider": self._pack_id,
                "engine": {"name": engine.name, "version": engine.version} if engine else None,
                "job_id": result.job_id,
                "duration_ms": result.duration_ms,
                "fidelity": result.fidelity,
            },
        )

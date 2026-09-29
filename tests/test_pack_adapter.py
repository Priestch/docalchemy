"""The pack adapter end to end: storage bridge, job protocol, upload,
normalization — against the real docling provider and a real StorageService.

Skipped when no provider is listening (e.g. CI without the sidecar), loud
when one is.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from app.domain.providers.contract import ProviderInput  # noqa: E402
from app.infrastructure.providers.docling.normalizer import (  # noqa: E402
    docling_raw_to_render_document,
)
from app.infrastructure.providers.pack.adapter import RemotePackAdapter  # noqa: E402
from app.infrastructure.providers.pack.normalizer import pack_raw_to_render_document  # noqa: E402
from app.infrastructure.storage import StorageService  # noqa: E402

PROVIDER_URL = "http://127.0.0.1:8099"
CORPUS = Path("/home/gaopeng/Enter/docalchemy/providers/provider_docling/tests/corpus/corpus.pdf")


def _provider_alive() -> bool:
    try:
        return httpx.get(f"{PROVIDER_URL}/health", timeout=2.0).is_success
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _provider_alive() or not CORPUS.exists(), reason="docling pack not running")


def test_pack_adapter_round_trip(tmp_path: Path) -> None:
    storage = StorageService(root_path=tmp_path / "storage")
    adapter = RemotePackAdapter(storage=storage, provider_url=PROVIDER_URL, pack_id="docling-pack")

    assert adapter.provider_version  # read from the provider's manifest
    assert "application/pdf" in adapter.supported_mime_types
    assert adapter.capabilities.has_table_extraction

    source_key = storage.save(CORPUS.read_bytes(), suffix=".pdf")
    output = adapter.execute(ProviderInput(source_storage_key=source_key, source_mime_type="application/pdf", config={}))

    by_type = {a.artifact_type: a for a in output.raw_artifacts}
    assert "normalized" in by_type, "the mapper input must be uploaded"
    assert "raw_json" in by_type, "the engine's lossless export must be uploaded"
    assert output.metadata["engine"]["name"] == "docling"

    # Every artifact's bytes resolve in storage.
    for artifact in output.raw_artifacts:
        assert storage.resolve(artifact.storage_key).is_file()

    # Normalized path: stored document -> RenderDocument.
    import json

    render = pack_raw_to_render_document(json.loads(storage.get(by_type["normalized"].storage_key)), {})
    assert render.blocks, "the render document must carry blocks"
    assert render.cell_bbox_mode == "text_extent"
    assert any(block.block_type == "table" for block in render.blocks)

    # Shadow check against the legacy normalizer on the same engine output.
    legacy = docling_raw_to_render_document(json.loads(storage.get(by_type["raw_json"].storage_key)), {})
    counts_a: dict[str, int] = {}
    counts_b: dict[str, int] = {}
    for block in legacy.blocks:
        counts_a[block.block_type] = counts_a.get(block.block_type, 0) + 1
    for block in render.blocks:
        counts_b[block.block_type] = counts_b.get(block.block_type, 0) + 1
    assert counts_a == counts_b

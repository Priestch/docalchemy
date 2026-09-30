"""Integration test for PackAdapter with Docker providers.

Run this after starting Docker providers:
    cd ~/Enter/docalchemy && docker compose up -d

Then run tests:
    pytest tests/integration/test_pack_adapter_integration.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.domain.providers.contract import ProviderInput
from app.infrastructure.providers.pack.adapter import PackAdapter
from app.infrastructure.storage import StorageService


@pytest.fixture
def storage(tmp_path: Path) -> StorageService:
    """Create a temporary storage service."""
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    return StorageService(root_path=storage_root)


@pytest.fixture
def test_pdf() -> Path:
    """Path to a test PDF file."""
    pdf_path = Path(__file__).parent.parent.parent / "fonduer/tests/data/pdf_simple/md.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found: {pdf_path}")
    return pdf_path


@pytest.fixture
def providers_running() -> bool:
    """Check if Docker providers are running."""
    import httpx

    try:
        response = httpx.get("http://localhost:8081/health", timeout=2.0)
        return response.is_success
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(
    not os.getenv("STORAGE_HOST_ROOT") or not os.getenv("STORAGE_PROVIDER_ROOT"),
    reason="Storage path env vars not set (STORAGE_HOST_ROOT, STORAGE_PROVIDER_ROOT)",
)
class TestPackAdapterWithDocker:
    """Tests for PackAdapter with Docker providers."""

    def test_auto_detect_path_mapping(self, storage: StorageService):
        """Test that path mapping is auto-detected from environment variables."""
        adapter = PackAdapter(
            storage=storage,
            provider_url="http://localhost:8081",
            pack_id="docling",
        )

        # Should have auto-detected mapping
        assert adapter._storage_path_mapping is not None
        host_root, provider_root = adapter._storage_path_mapping
        assert host_root == Path(os.getenv("STORAGE_HOST_ROOT"))
        assert provider_root == Path(os.getenv("STORAGE_PROVIDER_ROOT"))

    def test_adapter_connects_to_provider(self, storage: StorageService, providers_running: bool):
        """Test that adapter can connect and read provider manifest."""
        if not providers_running:
            pytest.skip("Docker providers not running")

        adapter = PackAdapter(
            storage=storage,
            provider_url="http://localhost:8081",
            pack_id="docling",
        )

        assert adapter.provider_id == "docling"
        assert adapter.provider_version
        assert len(adapter.supported_mime_types) > 0
        assert adapter.capabilities.has_ocr
        assert adapter.capabilities.has_table_extraction

    @pytest.mark.parametrize(
        "pack_id,provider_url",
        [
            ("docling", "http://localhost:8081"),
            ("mineru", "http://localhost:8082"),
            ("opendataloader", "http://localhost:8083"),
            ("franken_ocr", "http://localhost:8084"),
        ],
    )
    def test_all_providers_accessible(
        self, storage: StorageService, providers_running: bool, pack_id: str, provider_url: str
    ):
        """Test that all Docker providers are accessible."""
        if not providers_running:
            pytest.skip("Docker providers not running")

        adapter = PackAdapter(
            storage=storage,
            provider_url=provider_url,
            pack_id=pack_id,
        )

        assert adapter.provider_id == pack_id
        assert adapter.provider_version == "0.1.0"

    def test_parse_pdf_end_to_end(
        self, storage: StorageService, test_pdf: Path, providers_running: bool
    ):
        """Test complete PDF parsing workflow with docling provider."""
        if not providers_running:
            pytest.skip("Docker providers not running")

        # Use shared storage that Docker can access
        shared_storage_root = Path(os.getenv("STORAGE_HOST_ROOT"))
        shared_storage = StorageService(root_path=shared_storage_root)

        adapter = PackAdapter(
            storage=shared_storage,
            provider_url="http://localhost:8081",
            pack_id="docling",
        )

        # Save PDF to shared storage
        source_key = shared_storage.save(test_pdf.read_bytes(), suffix=".pdf")

        # Execute parsing
        output = adapter.execute(
            ProviderInput(
                source_storage_key=source_key,
                source_mime_type="application/pdf",
                config={},
            )
        )

        # Verify output
        assert len(output.raw_artifacts) >= 2  # At least normalized + raw_json
        assert output.metadata.get("engine", {}).get("name") == "docling"

        # Verify artifacts are in storage
        artifact_types = {a.artifact_type for a in output.raw_artifacts}
        assert "normalized" in artifact_types
        assert "raw_json" in artifact_types

        for artifact in output.raw_artifacts:
            artifact_path = shared_storage.resolve(artifact.storage_key)
            assert artifact_path.exists()
            assert artifact_path.stat().st_size > 0

    def test_manual_path_mapping_overrides_env(self, storage: StorageService):
        """Test that manual path mapping takes precedence over env vars."""
        manual_mapping = (Path("/custom/host"), Path("/custom/container"))

        adapter = PackAdapter(
            storage=storage,
            provider_url="http://localhost:8081",
            pack_id="docling",
            storage_path_mapping=manual_mapping,
        )

        assert adapter._storage_path_mapping == manual_mapping


@pytest.mark.unit
class TestPackAdapterUnit:
    """Unit tests for PackAdapter without Docker dependencies."""

    def test_adapter_initialization(self, storage: StorageService):
        """Test basic adapter initialization."""
        # This will fail if providers aren't running, but that's expected for unit tests
        with pytest.raises(Exception):
            PackAdapter(
                storage=storage,
                provider_url="http://localhost:9999",  # Non-existent
                pack_id="test",
            )

    def test_storage_path_mapping_optional(self, storage: StorageService):
        """Test that storage_path_mapping is optional."""
        # Clear env vars for this test
        old_host = os.getenv("STORAGE_HOST_ROOT")
        old_provider = os.getenv("STORAGE_PROVIDER_ROOT")

        try:
            if old_host:
                del os.environ["STORAGE_HOST_ROOT"]
            if old_provider:
                del os.environ["STORAGE_PROVIDER_ROOT"]

            # Should not raise, but will fail to connect
            with pytest.raises(Exception):
                adapter = PackAdapter(
                    storage=storage,
                    provider_url="http://localhost:9999",
                    pack_id="test",
                )
                # If it somehow connects, check mapping is None
                assert adapter._storage_path_mapping is None

        finally:
            # Restore env vars
            if old_host:
                os.environ["STORAGE_HOST_ROOT"] = old_host
            if old_provider:
                os.environ["STORAGE_PROVIDER_ROOT"] = old_provider

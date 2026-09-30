#!/usr/bin/env python
"""Quick test script to verify PackAdapter integration with Docker providers.

Usage:
    export STORAGE_HOST_ROOT=/home/gaopeng/localstorage/docalchemy
    export STORAGE_PROVIDER_ROOT=/storage
    python scripts/test_pack_integration.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.domain.providers.contract import ProviderInput
from app.infrastructure.providers.pack.adapter import PackAdapter
from app.infrastructure.storage import StorageService


def test_provider(pack_id: str, provider_url: str, storage: StorageService) -> bool:
    """Test a single provider."""
    print(f"\n{'='*60}")
    print(f"Testing {pack_id} at {provider_url}")
    print(f"{'='*60}")

    try:
        adapter = PackAdapter(
            storage=storage,
            provider_url=provider_url,
            pack_id=pack_id,
        )

        print(f"✓ Connected to {adapter.provider_id} v{adapter.provider_version}")
        print(f"  Capabilities:")
        print(f"    - OCR: {adapter.capabilities.has_ocr}")
        print(f"    - Tables: {adapter.capabilities.has_table_extraction}")
        print(f"    - Reading Order: {adapter.capabilities.has_reading_order}")
        print(f"  Supported MIME types: {len(adapter.supported_mime_types)}")

        # Check path mapping
        if adapter._storage_path_mapping:
            host, container = adapter._storage_path_mapping
            print(f"  Path mapping: {host} -> {container}")
        else:
            print(f"  ⚠ No path mapping configured")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_parse(storage: StorageService) -> bool:
    """Test actual PDF parsing."""
    print(f"\n{'='*60}")
    print(f"Testing PDF parsing with docling")
    print(f"{'='*60}")

    # Find test PDF
    test_pdf = Path("fonduer/tests/data/pdf_simple/md.pdf")
    if not test_pdf.exists():
        print(f"✗ Test PDF not found: {test_pdf}")
        return False

    try:
        adapter = PackAdapter(
            storage=storage,
            provider_url="http://localhost:8081",
            pack_id="docling",
        )

        # Save PDF to storage
        source_key = storage.save(test_pdf.read_bytes(), suffix=".pdf")
        print(f"✓ Saved test PDF to storage: {source_key[:40]}...")

        # Parse
        print(f"⏳ Parsing PDF...")
        output = adapter.execute(
            ProviderInput(
                source_storage_key=source_key,
                source_mime_type="application/pdf",
                config={},
            )
        )

        print(f"✓ Parse successful!")
        print(f"  Artifacts generated: {len(output.raw_artifacts)}")
        for artifact in output.raw_artifacts:
            artifact_path = storage.resolve(artifact.storage_key)
            size_kb = artifact_path.stat().st_size / 1024
            print(f"    - {artifact.artifact_type:15} ({artifact.format:4}) {size_kb:6.1f} KB")

        if output.metadata.get("engine"):
            engine = output.metadata["engine"]
            print(f"  Engine: {engine['name']} v{engine.get('version', 'unknown')}")

        duration = output.metadata.get("duration_ms")
        if duration:
            print(f"  Duration: {duration}ms")

        return True

    except Exception as e:
        print(f"✗ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    import os

    print("PackAdapter Integration Test")
    print("=" * 60)

    # Check environment variables
    host_root = os.getenv("STORAGE_HOST_ROOT")
    provider_root = os.getenv("STORAGE_PROVIDER_ROOT")

    if not host_root or not provider_root:
        print("⚠ WARNING: Storage path environment variables not set!")
        print("  Please export:")
        print("    export STORAGE_HOST_ROOT=/home/gaopeng/localstorage/docalchemy")
        print("    export STORAGE_PROVIDER_ROOT=/storage")
        print()
        print("  Tests will continue but path mapping won't work.")
        print()
    else:
        print(f"✓ Environment configured:")
        print(f"  STORAGE_HOST_ROOT={host_root}")
        print(f"  STORAGE_PROVIDER_ROOT={provider_root}")

    # Setup storage
    storage_root = Path(host_root) if host_root else Path("/tmp/test-storage")
    storage_root.mkdir(parents=True, exist_ok=True)
    storage = StorageService(root_path=storage_root)

    # Test all providers
    providers = [
        ("docling", "http://localhost:8081"),
        ("mineru", "http://localhost:8082"),
        ("opendataloader", "http://localhost:8083"),
        ("franken_ocr", "http://localhost:8084"),
    ]

    results = []
    for pack_id, url in providers:
        results.append((pack_id, test_provider(pack_id, url, storage)))

    # Test parsing
    parse_ok = test_parse(storage)

    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")

    for pack_id, ok in results:
        status = "✓" if ok else "✗"
        print(f"{status} {pack_id:20} {'PASS' if ok else 'FAIL'}")

    print(f"{'✓' if parse_ok else '✗'} PDF parsing          {'PASS' if parse_ok else 'FAIL'}")

    all_pass = all(ok for _, ok in results) and parse_ok
    print()
    if all_pass:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

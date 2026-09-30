"""Upload semantics under the storage_key/slug unique constraints.

Storage is content-addressed, so uploading the same bytes twice must return
the existing document, and a different file reusing a taken slug must get a
suffixed one — neither may surface as an integrity error.
"""

from __future__ import annotations

import pytest

from app.application.use_cases.upload_source_document import UploadSourceDocument
from app.infrastructure.storage import StorageService
from tests.fakes.fake_uow import FakeDocumentsUnitOfWork

PDF_BYTES = b"%PDF-1.4 minimal"

pytestmark = pytest.mark.asyncio


class MemoryStorage(StorageService):
    """StorageService that keeps bytes in a dict; save() is content-addressed."""

    def __init__(self) -> None:  # noqa: D107
        import tempfile
        from pathlib import Path

        super().__init__(root_path=Path(tempfile.mkdtemp()))
        self.files: dict[str, bytes] = {}

    def save(self, data: bytes, suffix: str = "") -> str:  # noqa: D102, ARG002
        import hashlib

        key = f"{hashlib.md5(data).hexdigest()}{suffix}"
        self.files[key] = data
        return key

    def get(self, key: str) -> bytes:  # noqa: D102
        return self.files[key]


@pytest.fixture
def uow() -> FakeDocumentsUnitOfWork:
    return FakeDocumentsUnitOfWork()


@pytest.fixture
def use_case(uow: FakeDocumentsUnitOfWork) -> UploadSourceDocument:
    return UploadSourceDocument(uow=uow, storage=MemoryStorage())


async def test_first_upload_creates_document(use_case: UploadSourceDocument) -> None:
    dto = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")

    assert dto.name == "report.pdf"
    assert dto.page_count == 0  # not a real PDF; extraction degrades gracefully


async def test_reupload_same_bytes_returns_existing(
    use_case: UploadSourceDocument, uow: FakeDocumentsUnitOfWork
) -> None:
    first = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")
    second = await use_case.execute(file_data=PDF_BYTES, filename="renamed.pdf", mime_type="application/pdf")

    assert second.id == first.id
    assert len(uow.documents._store) == 1  # noqa: SLF001 — one row, not a duplicate


async def test_different_file_with_taken_slug_gets_suffixed_slug(use_case: UploadSourceDocument) -> None:
    first = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")
    other = await use_case.execute(file_data=b"%PDF-1.4 different", filename="report.pdf", mime_type="application/pdf")

    assert other.id != first.id
    assert other.slug.startswith("report-")
    assert other.slug != first.slug

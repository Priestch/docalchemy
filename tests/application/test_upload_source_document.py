"""Upload semantics: every upload gets its own row, storage is shared.

Storage is content-addressed, so re-uploading the same bytes rewrites the
identical physical file while a second source_document row is created. Slugs
stay unique with numeric suffixes.
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
    assert dto.slug == "report"
    assert dto.page_count == 0  # not a real PDF; extraction degrades gracefully


async def test_reupload_same_bytes_creates_second_row_sharing_storage(
    use_case: UploadSourceDocument, uow: FakeDocumentsUnitOfWork
) -> None:
    first = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")
    second = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")

    assert second.id != first.id  # two upload records...
    assert second.storage_key == first.storage_key  # ...one physical file
    assert len(uow.documents._store) == 2  # noqa: SLF001


async def test_renamed_reupload_keeps_the_new_name(use_case: UploadSourceDocument) -> None:
    await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")
    second = await use_case.execute(file_data=PDF_BYTES, filename="renamed.pdf", mime_type="application/pdf")

    assert second.name == "renamed.pdf"
    assert second.slug == "renamed"


async def test_same_name_gets_numeric_slug_suffix(use_case: UploadSourceDocument) -> None:
    first = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")
    other = await use_case.execute(file_data=b"%PDF-1.4 different", filename="report.pdf", mime_type="application/pdf")

    assert other.slug == "report-2"
    assert other.storage_key != first.storage_key


async def test_slug_suffixes_increment(use_case: UploadSourceDocument) -> None:
    # Four uploads of the same name: report, report-2, report-3, report-4.
    for _ in range(3):
        await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")
    fourth = await use_case.execute(file_data=PDF_BYTES, filename="report.pdf", mime_type="application/pdf")

    assert fourth.slug == "report-4"

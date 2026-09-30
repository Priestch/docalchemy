from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.application.documents_uow import AbstractDocumentsUnitOfWork
from app.domain.documents.dtos import SourceDocumentDTO
from app.domain.documents.entities import PageDimensions, SourceDocument
from app.infrastructure.storage import StorageService


class UploadSourceDocument:
    def __init__(self, uow: AbstractDocumentsUnitOfWork, storage: StorageService) -> None:
        self._uow = uow
        self._storage = storage

    async def execute(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
    ) -> SourceDocumentDTO:
        suffix = Path(filename).suffix.lower()
        checksum = hashlib.md5(file_data).hexdigest()
        size_bytes = len(file_data)

        # Every upload gets its own row; storage stays content-addressed, so
        # re-uploading the same bytes just rewrites the identical file.
        storage_key = self._storage.save(file_data, suffix=suffix)

        page_count, page_dimensions = self._extract_page_info(file_data, mime_type, suffix)

        now = datetime.now(tz=timezone.utc)
        slug = await self._unique_slug(Path(filename).stem.lower().replace(" ", "-"))
        entity = SourceDocument(
            id=uuid4(),
            name=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            checksum=checksum,
            page_count=page_count,
            page_dimensions=page_dimensions,
            slug=slug,
            created_at=now,
            updated_at=now,
        )

        async with self._uow as uow:
            await uow.documents.add(entity)
            await uow.commit()

        return self._to_dto(entity)

    async def _unique_slug(self, slug: str) -> str:
        """Slugs back URLs and must stay unique; a taken name gets a numeric
        suffix (slug, slug-2, slug-3, ...) instead of an integrity error."""
        async with self._uow as uow:
            if await uow.documents.get_by_slug(slug) is None:
                return slug
            n = 2
            while await uow.documents.get_by_slug(f"{slug}-{n}") is not None:
                n += 1
            return f"{slug}-{n}"

    @staticmethod
    def _to_dto(entity: SourceDocument) -> SourceDocumentDTO:
        return SourceDocumentDTO(
            id=entity.id,
            name=entity.name,
            mime_type=entity.mime_type,
            size_bytes=entity.size_bytes,
            storage_key=entity.storage_key,
            checksum=entity.checksum,
            page_count=entity.page_count,
            page_dimensions=entity.page_dimensions,
            slug=entity.slug,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _extract_page_info(
        self, file_data: bytes, mime_type: str, suffix: str
    ) -> tuple[int, list[PageDimensions]]:
        if mime_type != "application/pdf":
            return 0, []
        try:
            return self._get_pdf_page_info(file_data)
        except Exception:
            return 0, []

    @staticmethod
    def _get_pdf_page_info(file_data: bytes) -> tuple[int, list[PageDimensions]]:
        from PyPDF2 import PdfReader
        import io

        reader = PdfReader(io.BytesIO(file_data))
        dimensions = []
        for i, page in enumerate(reader.pages):
            box = page.mediabox
            width = float(box.width)
            height = float(box.height)
            dimensions.append(PageDimensions(page_index=i, width=width, height=height))
        return len(reader.pages), dimensions

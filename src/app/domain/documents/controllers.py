from __future__ import annotations

from typing import Annotated
from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import File as FileResponse

from app.application.use_cases.upload_source_document import UploadSourceDocument
from app.domain.analysis.dependencies import provide_analysis_uow
from app.domain.documents.dependencies import (
    provide_documents_uow,
    provide_storage_service,
    provide_upload_source_document,
)
from app.domain.documents.dtos import SourceDocumentDTO, SourceDocumentListDTO, LatestRunSummary, DocumentRunsDTO
from app.infrastructure.storage import StorageService
from app.infrastructure.uow import SqlAlchemyAnalysisUnitOfWork, SqlAlchemyDocumentsUnitOfWork


class DocumentController(Controller):
    path = "documents"

    dependencies = {
        "documents_uow": Provide(provide_documents_uow),
        "storage_service": Provide(provide_storage_service),
        "upload_use_case": Provide(provide_upload_source_document),
    }

    @post()
    async def upload(
        self,
        upload_use_case: UploadSourceDocument,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> SourceDocumentDTO:
        file_data = await data.read()
        return await upload_use_case.execute(
            file_data=file_data,
            filename=data.filename,
            mime_type=data.content_type,
        )

    @get(dependencies={"analysis_uow": Provide(provide_analysis_uow)})
    async def list_documents(
        self,
        documents_uow: SqlAlchemyDocumentsUnitOfWork,
        analysis_uow: SqlAlchemyAnalysisUnitOfWork,
        offset: int = 0,
        limit: int = 50,
    ) -> SourceDocumentListDTO:
        async with documents_uow:
            docs = await documents_uow.documents.list(offset=offset, limit=limit)
            total = await documents_uow.documents.count()

        doc_ids = [d.id for d in docs]
        document_runs: list[DocumentRunsDTO] = []

        if doc_ids:
            async with analysis_uow:
                for doc_id in doc_ids:
                    runs = await analysis_uow.runs.get_by_document(doc_id)
                    seen_providers: set[str] = set()
                    summaries: list[LatestRunSummary] = []
                    for run in runs:
                        if run.provider_id not in seen_providers:
                            seen_providers.add(run.provider_id)
                            summaries.append(LatestRunSummary(
                                id=run.id,
                                provider_id=run.provider_id,
                                status=str(run.status),
                                created_at=run.created_at,
                            ))
                    if summaries:
                        document_runs.append(DocumentRunsDTO(
                            document_id=doc_id,
                            runs=summaries,
                        ))

        return SourceDocumentListDTO(
            items=[
                SourceDocumentDTO(
                    id=d.id,
                    name=d.name,
                    mime_type=d.mime_type,
                    size_bytes=d.size_bytes,
                    storage_key=d.storage_key,
                    checksum=d.checksum,
                    page_count=d.page_count,
                    page_dimensions=d.page_dimensions,
                    slug=d.slug,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                )
                for d in docs
            ],
            document_runs=document_runs,
            total=total,
            offset=offset,
            limit=limit,
        )

    @get("/{document_id:uuid}")
    async def get_document(
        self,
        document_id: UUID,
        documents_uow: SqlAlchemyDocumentsUnitOfWork,
    ) -> SourceDocumentDTO:
        async with documents_uow:
            doc = await documents_uow.documents.get(document_id)

        return SourceDocumentDTO(
            id=doc.id,
            name=doc.name,
            mime_type=doc.mime_type,
            size_bytes=doc.size_bytes,
            storage_key=doc.storage_key,
            checksum=doc.checksum,
            page_count=doc.page_count,
            page_dimensions=doc.page_dimensions,
            slug=doc.slug,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    @get("/{document_id:uuid}/download")
    async def download(
        self,
        document_id: UUID,
        documents_uow: SqlAlchemyDocumentsUnitOfWork,
        storage_service: StorageService,
    ) -> FileResponse:
        async with documents_uow:
            doc = await documents_uow.documents.get(document_id)

        file_path = storage_service.resolve(doc.storage_key)
        return FileResponse(path=file_path, filename=doc.name)

    @delete("/{document_id:uuid}")
    async def delete_document(
        self,
        document_id: UUID,
        documents_uow: SqlAlchemyDocumentsUnitOfWork,
        storage_service: StorageService,
    ) -> None:
        async with documents_uow:
            doc = await documents_uow.documents.get(document_id)
            storage_path = storage_service.resolve(doc.storage_key)
            storage_path.unlink(missing_ok=True)
            await documents_uow.documents.delete(document_id)

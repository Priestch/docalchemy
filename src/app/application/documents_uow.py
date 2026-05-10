from __future__ import annotations

from app.application.unit_of_work import AbstractUnitOfWork
from app.domain.documents.repositories import AbstractSourceDocumentRepository


class AbstractDocumentsUnitOfWork(AbstractUnitOfWork):
    documents: AbstractSourceDocumentRepository

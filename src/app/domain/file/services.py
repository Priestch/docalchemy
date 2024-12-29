from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
)

from app.db.models import File
from app.domain.file.repositories import FileRepository


class FileService(SQLAlchemyAsyncRepositoryService[File]):
    repository_type = FileRepository

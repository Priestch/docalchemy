from advanced_alchemy.repository import SQLAlchemyAsyncSlugRepository

from app.db.models import File


class FileRepository(SQLAlchemyAsyncSlugRepository[File]):
    model_type = File

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.file.services import FileService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession


async def provide_files_service(db_session: AsyncSession) -> AsyncGenerator[FileService, None]:
    """Construct repository and service objects for the request."""
    async with FileService.new(
        session=db_session,
    ) as service:
        yield service

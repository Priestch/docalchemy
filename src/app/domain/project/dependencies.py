from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.project.services import ProjectService

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["provide_project_service"]


async def provide_project_service(
    db_session: AsyncSession | None = None,
) -> AsyncGenerator[ProjectService, None]:
    """Provide Tags service.

    Args:
        db_session (AsyncSession | None, optional): current database session. Defaults to None.

    Returns:
        TagService: An Tags service object
    """
    async with ProjectService.new(
        session=db_session,
    ) as service:
        yield service

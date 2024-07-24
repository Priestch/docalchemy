from app.lib.schema import CamelizedBaseStruct

from uuid import UUID  # noqa: TCH003


class Project(CamelizedBaseStruct):
    """User properties to use for a response."""

    id: UUID
    name: str
    store_key: str
    owner: str
    status: int

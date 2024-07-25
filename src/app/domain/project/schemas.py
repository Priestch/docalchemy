from uuid import UUID

from app.lib.schema import CamelizedBaseStruct


class Project(CamelizedBaseStruct):
    """User properties to use for a response."""

    id: UUID
    name: str
    store_key: str
    owner: str
    status: int

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class File(UUIDAuditBase):
    name: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[int] = mapped_column(default=0)
    md5_hash: Mapped[str] = mapped_column(nullable=False, default="")


class DocElement(UUIDAuditBase):
    doc_id: Mapped[str] = mapped_column(ForeignKey("doc.id"), nullable=False)
    data: Mapped[dict]


class AnalysedDoc(UUIDAuditBase):
    file_id: Mapped[str] = mapped_column(ForeignKey("file.id"), nullable=False)
    analysed_by: Mapped[int]

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RenderBoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class RenderBlock(BaseModel):
    id: str
    block_type: str
    text: str = ""
    heading_level: int | None = None
    bbox: RenderBoundingBox | None = None
    page_index: int
    reading_order: int = 0
    confidence: float | None = None
    children: list[str] = Field(default_factory=list)


class RenderCell(BaseModel):
    row_index: int
    col_index: int
    row_span: int = 1
    col_span: int = 1
    text: str = ""
    bbox: RenderBoundingBox | None = None
    is_header: bool = False


class RenderTable(BaseModel):
    block_id: str
    rows: int
    cols: int
    cells: list[RenderCell] = Field(default_factory=list)


class RenderFigure(BaseModel):
    block_id: str
    image_storage_key: str | None = None
    description: str | None = None


class RenderPage(BaseModel):
    page_index: int
    width: float
    height: float
    children: list[str] = Field(default_factory=list)


class RenderDocument(BaseModel):
    provider_metadata: dict = Field(default_factory=dict)
    cell_bbox_mode: Literal["exact", "text_extent", "none"] = "none"
    pages: list[RenderPage] = Field(default_factory=list)
    blocks: list[RenderBlock] = Field(default_factory=list)
    tables: list[RenderTable] = Field(default_factory=list)
    figures: list[RenderFigure] = Field(default_factory=list)
    reading_order: list[str] = Field(default_factory=list)

"""Document (contract) -> RenderDocument (frontend contract) mapping."""

from __future__ import annotations

from docalchemy.contract import Document, ElementKind
from docalchemy.contract.document import BBox, TableCell

from app.infrastructure.render_document import (
    RenderBlock,
    RenderBoundingBox,
    RenderCell,
    RenderDocument,
    RenderFigure,
    RenderPage,
    RenderTable,
)

_KIND_TO_TYPE: dict[str, str] = {
    ElementKind.TEXT.value: "paragraph",
    ElementKind.HEADING.value: "heading",
    ElementKind.LIST.value: "list_item",
    ElementKind.TABLE.value: "table",
    ElementKind.FIGURE.value: "figure",
    ElementKind.FORMULA.value: "formula",
    ElementKind.CAPTION.value: "caption",
    ElementKind.FOOTNOTE.value: "footnote",
    ElementKind.CODE.value: "code",
    ElementKind.PAGE_HEADER.value: "page_header",
    ElementKind.PAGE_FOOTER.value: "page_footer",
    # key_value has no counterpart in the render vocabulary; it degrades to a
    # paragraph rather than being dropped — the text is real, the structure
    # interpretation is what the kind carried.
    ElementKind.KEY_VALUE.value: "paragraph",
}


def _bbox(bbox: BBox | None) -> RenderBoundingBox | None:
    if bbox is None:
        return None
    return RenderBoundingBox(x0=bbox.x0, y0=bbox.y0, x1=bbox.x1, y1=bbox.y1)


def _cell(cell: TableCell) -> RenderCell:
    return RenderCell(
        row_index=cell.row,
        col_index=cell.col,
        row_span=cell.row_span,
        col_span=cell.col_span,
        text=cell.text,
        bbox=_bbox(cell.bbox),
        is_header=cell.is_header,
    )


def document_to_render_document(document: Document) -> RenderDocument:
    """A pure translation: same information, the render contract's shape."""
    ordered = sorted(document.blocks, key=lambda block: block.order)
    tables_by_id = {table.id: table for table in document.tables}

    blocks: list[RenderBlock] = []
    tables: list[RenderTable] = []
    figures: list[RenderFigure] = []
    for block in ordered:
        blocks.append(
            RenderBlock(
                id=block.id,
                block_type=_KIND_TO_TYPE.get(block.kind.value, "paragraph"),
                text=block.text,
                heading_level=block.level,
                bbox=_bbox(block.bbox),
                page_index=block.page,
                reading_order=block.order,
                confidence=block.confidence,
            )
        )
        table = tables_by_id.get(block.id)
        if table is not None:
            tables.append(
                RenderTable(
                    block_id=table.id,
                    rows=table.rows,
                    cols=table.cols,
                    cells=[_cell(cell) for cell in table.cells],
                )
            )
        if block.artifact_id:
            figures.append(
                RenderFigure(
                    block_id=block.id,
                    image_storage_key=block.artifact_id,
                    description=block.text or None,
                )
            )

    pages = [
        RenderPage(page_index=page.index, width=page.width, height=page.height)
        for page in document.pages
    ]

    return RenderDocument(
        provider_metadata=document.metadata,
        cell_bbox_mode=document.cell_bbox_mode,
        pages=pages,
        blocks=blocks,
        tables=tables,
        figures=figures,
        reading_order=[block.id for block in ordered],
    )

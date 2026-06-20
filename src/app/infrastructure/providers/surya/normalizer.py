from __future__ import annotations

from app.infrastructure.render_document import (
    RenderBlock,
    RenderBoundingBox,
    RenderCell,
    RenderDocument,
    RenderFigure,
    RenderPage,
    RenderTable,
)

LABEL_MAP: dict[str, str] = {
    "Text": "paragraph",
    "SectionHeader": "heading",
    "Table": "table",
    "Picture": "figure",
    "Figure": "figure",
    "Equation": "formula",
    "Formula": "formula",
    "ListGroup": "list_item",
    "Caption": "caption",
    "PageHeader": "page_header",
    "PageFooter": "page_footer",
    "Code": "code",
    "Footnote": "footnote",
    "Form": "paragraph",
    "TableOfContents": "paragraph",
    "Bibliography": "paragraph",
    "Diagram": "figure",
    "ChemicalBlock": "figure",
}


def surya_raw_to_render_document(
    raw_json: list[dict] | dict,
    provider_metadata: dict,
) -> RenderDocument:
    if isinstance(raw_json, dict):
        pages_data = raw_json.get("pages", [raw_json])
    else:
        pages_data = raw_json

    pages = _extract_pages(pages_data)
    block_map: dict[str, RenderBlock] = {}
    tables: list[RenderTable] = []
    figures: list[RenderFigure] = []
    reading_order: list[str] = []

    for page_data in pages_data:
        page_idx = page_data.get("page_index", 0)
        blocks = page_data.get("blocks", [])

        for block in blocks:
            rb = _block_to_render_block(block, page_idx, pages)
            if rb is not None:
                block_map[rb.id] = rb
                reading_order.append(rb.id)

                if rb.block_type == "table":
                    t = _block_to_table(block, rb.id)
                    if t is not None:
                        tables.append(t)
                elif rb.block_type == "figure":
                    f = _block_to_figure(block, rb.id)
                    if f is not None:
                        figures.append(f)

    for page in pages:
        page.children = [bid for bid, b in block_map.items() if b.page_index == page.page_index]

    return RenderDocument(
        provider_metadata=provider_metadata,
        pages=pages,
        blocks=list(block_map.values()),
        tables=tables,
        figures=figures,
        reading_order=reading_order,
    )


def _extract_pages(pages_data: list[dict]) -> list[RenderPage]:
    pages = []
    for p in pages_data:
        page_idx = p.get("page_index", 0)
        width = float(p.get("page_width", p.get("width", 612.0)))
        height = float(p.get("page_height", p.get("height", 792.0)))
        pages.append(RenderPage(page_index=page_idx, width=width, height=height))

    if not pages:
        pages.append(RenderPage(page_index=0, width=612.0, height=792.0))

    pages.sort(key=lambda x: x.page_index)
    return pages


def _get_bbox(block: dict, page: RenderPage) -> RenderBoundingBox | None:
    bbox_data = block.get("bbox", block.get("polygon"))
    if bbox_data is None:
        return None

    if isinstance(bbox_data, list):
        if len(bbox_data) == 4:
            if isinstance(bbox_data[0], (int, float)):
                x0, y0, x1, y1 = bbox_data
            elif isinstance(bbox_data[0], (list, tuple)):
                xs = [p[0] for p in bbox_data]
                ys = [p[1] for p in bbox_data]
                x0, y0 = min(xs), min(ys)
                x1, y1 = max(xs), max(ys)
            else:
                return None
        else:
            return None
    else:
        return None

    return RenderBoundingBox(
        x0=max(0.0, min(1.0, x0 / page.width if page.width else 0)),
        y0=max(0.0, min(1.0, y0 / page.height if page.height else 0)),
        x1=max(0.0, min(1.0, x1 / page.width if page.width else 0)),
        y1=max(0.0, min(1.0, y1 / page.height if page.height else 0)),
    )


def _block_to_render_block(block: dict, page_idx: int, pages: list[RenderPage]) -> RenderBlock | None:
    label = block.get("label", "Text")
    block_type = LABEL_MAP.get(label, "paragraph")

    page = pages[page_idx] if page_idx < len(pages) else pages[0]
    bbox = _get_bbox(block, page)

    block_id = str(block.get("id", block.get("block_id", block.get("obj_id", ""))))
    if not block_id:
        block_id = f"surya_blk_{page_idx}_{block.get('reading_order', id(block))}"

    text = block.get("text", block.get("html", ""))
    if isinstance(text, (dict, list)):
        text = str(text)

    heading_level = None
    if block_type == "heading":
        heading_level = 1

    reading_order_val = block.get("reading_order", block.get("position", 0))

    confidence = block.get("confidence")

    return RenderBlock(
        id=block_id,
        block_type=block_type,
        text=str(text) if text else "",
        heading_level=heading_level,
        bbox=bbox,
        page_index=page_idx,
        reading_order=reading_order_val,
        confidence=confidence,
    )


def _block_to_table(block: dict, block_id: str) -> RenderTable | None:
    html = block.get("html", "")
    if not html:
        rows = block.get("rows", block.get("num_rows", 0))
        cols = block.get("cols", block.get("num_cols", 0))
        cells = block.get("cells", [])
        if not cells:
            return RenderTable(block_id=block_id, rows=rows or 0, cols=cols or 0)

        render_cells = []
        for cell in cells:
            render_cells.append(
                RenderCell(
                    row_index=cell.get("row_id", cell.get("row", cell.get("row_index", 0))),
                    col_index=cell.get("col_id", cell.get("col", cell.get("col_index", 0))),
                    row_span=cell.get("row_span", 1),
                    col_span=cell.get("col_span", 1),
                    text=str(cell.get("text", cell.get("html", ""))),
                    is_header=cell.get("is_header", False),
                )
            )

        max_row = max(c.row_index + c.row_span for c in render_cells) if render_cells else 1
        max_col = max(c.col_index + c.col_span for c in render_cells) if render_cells else 1
        return RenderTable(block_id=block_id, rows=max_row, cols=max_col, cells=render_cells)

    from html.parser import HTMLParser

    class TableParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.cells: list[RenderCell] = []
            self._row = 0
            self._col = 0
            self._in_cell = False
            self._cell_text: list[str] = []
            self._is_header = False
            self._max_row = 0
            self._max_col = 0

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            if tag == "tr":
                self._col = 0
            elif tag in ("td", "th"):
                self._in_cell = True
                self._cell_text = []
                self._is_header = tag == "th"
                row_span = 1
                col_span = 1
                for name, val in attrs:
                    if name == "rowspan":
                        row_span = int(val)
                    elif name == "colspan":
                        col_span = int(val)
                self._current_row_span = row_span
                self._current_col_span = col_span

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag in ("td", "th"):
                self._in_cell = False
                text = "".join(self._cell_text).strip()
                self.cells.append(
                    RenderCell(
                        row_index=self._row,
                        col_index=self._col,
                        row_span=self._current_row_span,
                        col_span=self._current_col_span,
                        text=text,
                        is_header=self._is_header,
                    )
                )
                self._max_row = max(self._max_row, self._row + self._current_row_span)
                self._max_col = max(self._max_col, self._col + self._current_col_span)
                self._col += self._current_col_span

        def handle_data(self, data):
            if self._in_cell:
                self._cell_text.append(data)

    parser = TableParser()
    parser.feed(html)

    if not parser.cells:
        return RenderTable(block_id=block_id, rows=0, cols=0)

    return RenderTable(
        block_id=block_id,
        rows=parser._max_row,
        cols=parser._max_col,
        cells=parser.cells,
    )


def _block_to_figure(block: dict, block_id: str) -> RenderFigure | None:
    description = block.get("text", block.get("html", block.get("caption", "")))
    if isinstance(description, (dict, list)):
        description = str(description)

    return RenderFigure(
        block_id=block_id,
        image_storage_key=None,
        description=str(description) if description else None,
    )

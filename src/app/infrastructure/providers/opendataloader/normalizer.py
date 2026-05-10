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

TYPE_MAP: dict[str, str] = {
    "heading": "heading",
    "paragraph": "paragraph",
    "table": "table",
    "image": "figure",
    "list": "list_item",
    "caption": "caption",
    "formula": "formula",
    "page_header": "page_header",
    "page_footer": "page_footer",
}


def opendataloader_raw_to_render_document(
    raw_json: list[dict],
    provider_metadata: dict,
    page_dimensions: list[dict] | None = None,
) -> RenderDocument:
    if isinstance(raw_json, dict):
        elements = raw_json.get("elements", raw_json.get("content", []))
        if isinstance(elements, list):
            raw_json = elements
        elif isinstance(raw_json, list):
            raw_json = raw_json
        else:
            raw_json = []

    pages = _build_pages(raw_json, page_dimensions)
    blocks: list[RenderBlock] = []
    tables: list[RenderTable] = []
    figures: list[RenderFigure] = []
    reading_order: list[str] = []

    for idx, element in enumerate(raw_json):
        block = _element_to_block(element, idx, pages)
        if block is not None:
            blocks.append(block)
            reading_order.append(block.id)

            if block.block_type == "table":
                table = _element_to_table(element, block.id)
                if table is not None:
                    tables.append(table)
            elif block.block_type == "figure":
                figure = _element_to_figure(element, block.id)
                if figure is not None:
                    figures.append(figure)

    for page in pages:
        page.children = [b.id for b in blocks if b.page_index == page.page_index]

    return RenderDocument(
        provider_metadata=provider_metadata,
        pages=pages,
        blocks=blocks,
        tables=tables,
        figures=figures,
        reading_order=reading_order,
    )


def _build_pages(elements: list[dict], page_dimensions: list[dict] | None) -> list[RenderPage]:
    page_dims_map: dict[int, tuple[float, float]] = {}
    if page_dimensions:
        for pd in page_dimensions:
            page_dims_map[pd.get("page_index", 0)] = (pd.get("width", 612.0), pd.get("height", 792.0))

    page_indices: set[int] = set()
    for el in elements:
        page_no = el.get("page_number", el.get("page", 1))
        if isinstance(page_no, int):
            page_indices.add(max(0, page_no - 1))

    if not page_indices:
        page_indices = {0}

    pages = []
    for pi in sorted(page_indices):
        w, h = page_dims_map.get(pi, (612.0, 792.0))
        pages.append(RenderPage(page_index=pi, width=w, height=h))
    return pages


def _get_page_index(element: dict) -> int:
    page_no = element.get("page_number", element.get("page", 1))
    if isinstance(page_no, int):
        return max(0, page_no - 1)
    return 0


def _normalize_bbox(
    bbox_data: list | dict | None,
    page: RenderPage,
) -> RenderBoundingBox | None:
    if bbox_data is None:
        return None

    if isinstance(bbox_data, dict):
        coords = bbox_data.get("bbox", bbox_data.get("bounding_box"))
        if coords is None:
            return None
        bbox_data = coords

    if not isinstance(bbox_data, (list, tuple)) or len(bbox_data) < 4:
        return None

    left, bottom, right, top = bbox_data[:4]

    y0_raw = page.height - top
    y1_raw = page.height - bottom

    x0 = left / page.width if page.width else 0
    y0 = y0_raw / page.height if page.height else 0
    x1 = right / page.width if page.width else 0
    y1 = y1_raw / page.height if page.height else 0

    return RenderBoundingBox(
        x0=max(0.0, min(1.0, x0)),
        y0=max(0.0, min(1.0, y0)),
        x1=max(0.0, min(1.0, x1)),
        y1=max(0.0, min(1.0, y1)),
    )


def _element_to_block(element: dict, order: int, pages: list[RenderPage]) -> RenderBlock | None:
    el_type = element.get("type", "paragraph")
    block_type = TYPE_MAP.get(el_type, "paragraph")

    page_idx = _get_page_index(element)
    page = pages[page_idx] if page_idx < len(pages) else pages[0]

    bbox_data = element.get("bounding_box", element.get("bbox"))
    bbox = _normalize_bbox(bbox_data, page)

    el_id = str(element.get("id", f"el_{order}"))

    text = element.get("content", element.get("text", ""))
    if isinstance(text, dict):
        text = text.get("text", str(text))

    heading_level = None
    if block_type == "heading":
        heading_level = element.get("heading_level", element.get("level", 1))
        if not isinstance(heading_level, int):
            heading_level = 1

    confidence = element.get("confidence")

    return RenderBlock(
        id=el_id,
        block_type=block_type,
        text=str(text),
        heading_level=heading_level,
        bbox=bbox,
        page_index=page_idx,
        reading_order=order,
        confidence=confidence,
    )


def _element_to_table(element: dict, block_id: str) -> RenderTable | None:
    table_data = element.get("table", element.get("data", element.get("cells")))
    if not table_data:
        return RenderTable(block_id=block_id, rows=0, cols=0)

    if isinstance(table_data, list) and table_data and isinstance(table_data[0], list):
        rows = len(table_data)
        cols = max(len(row) for row in table_data) if table_data else 0
        cells = []
        for ri, row in enumerate(table_data):
            for ci, cell in enumerate(row):
                cell_text = cell.get("text", str(cell)) if isinstance(cell, dict) else str(cell)
                is_header = cell.get("is_header", ri == 0) if isinstance(cell, dict) else ri == 0
                cells.append(
                    RenderCell(
                        row_index=ri,
                        col_index=ci,
                        text=cell_text,
                        is_header=is_header,
                    )
                )
        return RenderTable(block_id=block_id, rows=rows, cols=cols, cells=cells)

    if isinstance(table_data, dict):
        rows = table_data.get("rows", 0)
        cols = table_data.get("cols", 0)
        raw_cells = table_data.get("cells", [])
        cells = []
        for cell in raw_cells:
            cells.append(
                RenderCell(
                    row_index=cell.get("row", cell.get("row_index", 0)),
                    col_index=cell.get("col", cell.get("col_index", 0)),
                    text=cell.get("text", ""),
                    is_header=cell.get("is_header", False),
                )
            )
        return RenderTable(block_id=block_id, rows=rows, cols=cols, cells=cells)

    return None


def _element_to_figure(element: dict, block_id: str) -> RenderFigure | None:
    description = element.get("description", element.get("caption", element.get("content", None)))
    image_key = element.get("image_path", None)
    return RenderFigure(
        block_id=block_id,
        image_storage_key=image_key,
        description=description,
    )

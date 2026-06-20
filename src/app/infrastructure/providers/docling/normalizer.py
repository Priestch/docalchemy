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
    "paragraph": "paragraph",
    "title": "heading",
    "section_header": "heading",
    "table": "table",
    "picture": "figure",
    "list_item": "list_item",
    "caption": "caption",
    "formula": "formula",
    "page_header": "page_header",
    "page_footer": "page_footer",
    "code": "code",
    "reference": "paragraph",
    "footnote": "footnote",
}


def docling_raw_to_render_document(
    raw_json: dict,
    provider_metadata: dict,
) -> RenderDocument:
    pages = _extract_pages(raw_json)
    block_map: dict[str, RenderBlock] = {}
    tables: list[RenderTable] = []
    figures: list[RenderFigure] = []
    reading_order: list[str] = []

    texts = raw_json.get("texts", [])
    for text_item in texts:
        block = _text_to_block(text_item, pages)
        if block is not None:
            block_map[block.id] = block

    any_cell_has_bbox = False
    for table_item in raw_json.get("tables", []):
        table_block, table, has_bbox = _table_to_block_and_table(table_item, pages)
        if table_block is not None:
            block_map[table_block.id] = table_block
        if table is not None:
            tables.append(table)
        if has_bbox:
            any_cell_has_bbox = True

    for picture_item in raw_json.get("pictures", []):
        fig_block, figure = _picture_to_block_and_figure(picture_item, pages)
        if fig_block is not None:
            block_map[fig_block.id] = fig_block
        if figure is not None:
            figures.append(figure)

    body = raw_json.get("main-text", raw_json.get("body", {}))
    children_refs = body.get("children", [])
    order_idx = 0
    for ref in children_refs:
        ref_id = _resolve_ref(ref, raw_json)
        if ref_id and ref_id in block_map:
            block_map[ref_id].reading_order = order_idx
            reading_order.append(ref_id)
            order_idx += 1

    for page in pages:
        page.children = [
            bid for bid, b in block_map.items() if b.page_index == page.page_index
        ]

    return RenderDocument(
        provider_metadata=provider_metadata,
        cell_bbox_mode="text_extent" if any_cell_has_bbox else "none",
        pages=pages,
        blocks=list(block_map.values()),
        tables=tables,
        figures=figures,
        reading_order=reading_order,
    )


def _extract_pages(raw_json: dict) -> list[RenderPage]:
    pages_data = raw_json.get("pages", {})
    pages = []
    for page_key, page_info in pages_data.items():
        if isinstance(page_info, dict):
            raw_page = page_info.get("page", int(page_key) if page_key.isdigit() else 0)
            page_index = max(0, raw_page - 1)
            width = page_info.get("size", {}).get("width", 612.0)
            height = page_info.get("size", {}).get("height", 792.0)
            pages.append(
                RenderPage(
                    page_index=page_index,
                    width=width,
                    height=height,
                ),
            )
    if not pages:
        pages.append(RenderPage(page_index=0, width=612.0, height=792.0))
    return pages


def _get_page_for_block(
    prov: list, pages: list[RenderPage],
) -> tuple[int, RenderBoundingBox | None]:
    if not prov:
        return 0, None
    first_prov = prov[0]
    page_no = first_prov.get("page_no", first_prov.get("page", 1)) - 1
    page_idx = max(0, min(page_no, len(pages) - 1))
    page = pages[page_idx]

    bbox_data = first_prov.get("bbox")
    if not bbox_data:
        return page_idx, None

    coord_origin = first_prov.get("coord_origin", "BOTTOMLEFT")
    l, t, r, b = bbox_data.get("l", 0), bbox_data.get("t", 0), bbox_data.get("r", 0), bbox_data.get("b", 0)

    if coord_origin == "BOTTOMLEFT":
        y0_raw = page.height - t
        y1_raw = page.height - b
    else:
        y0_raw = t
        y1_raw = b

    x0 = l / page.width if page.width else 0
    y0 = y0_raw / page.height if page.height else 0
    x1 = r / page.width if page.width else 0
    y1 = y1_raw / page.height if page.height else 0

    return page_idx, RenderBoundingBox(
        x0=max(0.0, min(1.0, x0)),
        y0=max(0.0, min(1.0, y0)),
        x1=max(0.0, min(1.0, x1)),
        y1=max(0.0, min(1.0, y1)),
    )


def _cell_bbox_to_render(
    cell_bbox: dict | None, page: RenderPage,
) -> RenderBoundingBox | None:
    """Convert a Docling table-cell bbox (page-pixel dict with l/t/r/b) to a
    normalized RenderBoundingBox. Docling cells carry their own ``bbox`` dict
    (unlike block-level ``prov``), so this is separate from
    ``_get_page_for_block``. Origin is BOTTOMLEFT (y-up from bottom); we store
    y as distance-from-top (y-down) to match the rest of the render doc.
    """
    if not isinstance(cell_bbox, dict):
        return None
    if not ({"l", "t", "r", "b"} <= cell_bbox.keys()):
        return None

    coord_origin = cell_bbox.get("coord_origin", "BOTTOMLEFT")
    l = cell_bbox.get("l", 0)
    t = cell_bbox.get("t", 0)
    r = cell_bbox.get("r", 0)
    b = cell_bbox.get("b", 0)

    if coord_origin == "BOTTOMLEFT":
        y0_raw = (page.height - t) if page.height else 0
        y1_raw = (page.height - b) if page.height else 0
    else:
        y0_raw = t
        y1_raw = b

    x0 = l / page.width if page.width else 0
    y0 = y0_raw / page.height if page.height else 0
    x1 = r / page.width if page.width else 0
    y1 = y1_raw / page.height if page.height else 0

    return RenderBoundingBox(
        x0=max(0.0, min(1.0, min(x0, x1))),
        y0=max(0.0, min(1.0, min(y0, y1))),
        x1=max(0.0, min(1.0, max(x0, x1))),
        y1=max(0.0, min(1.0, max(y0, y1))),
    )


def _text_to_block(text_item: dict, pages: list[RenderPage]) -> RenderBlock | None:
    text = text_item.get("text", "")
    label = text_item.get("label", "paragraph")
    block_type = LABEL_MAP.get(label, "paragraph")
    prov = text_item.get("prov", [])
    page_idx, bbox = _get_page_for_block(prov, pages)

    heading_level = None
    if block_type == "heading":
        heading_level = 1
        if label == "section_header":
            heading_level = 2

    block_id = str(text_item.get("self_ref", text_item.get("obj_id", "")))
    if not block_id:
        block_id = f"txt_{id(text_item)}"

    confidence = text_item.get("confidence")
    return RenderBlock(
        id=block_id,
        block_type=block_type,
        text=text,
        heading_level=heading_level,
        bbox=bbox,
        page_index=page_idx,
        confidence=confidence,
    )


def _table_to_block_and_table(
    table_item: dict, pages: list[RenderPage],
) -> tuple[RenderBlock | None, RenderTable | None, bool]:
    prov = table_item.get("prov", [])
    page_idx, bbox = _get_page_for_block(prov, pages)

    block_id = str(table_item.get("self_ref", table_item.get("obj_id", "")))
    if not block_id:
        block_id = f"tbl_{id(table_item)}"

    text = table_item.get("text", "")
    block = RenderBlock(
        id=block_id,
        block_type="table",
        text=text[:200] if text else "",
        bbox=bbox,
        page_index=page_idx,
    )

    data = table_item.get("data", {})
    grid = data.get("grid", [])
    if not grid:
        return block, RenderTable(block_id=block_id, rows=0, cols=0), False

    # Flatten grid: Docling may return nested lists or flat cell dicts
    flat_cells = []
    for item in grid:
        if isinstance(item, list):
            for cell in item:
                if isinstance(cell, dict):
                    flat_cells.append(cell)
        elif isinstance(item, dict):
            flat_cells.append(item)

    if not flat_cells:
        return block, RenderTable(block_id=block_id, rows=0, cols=0), False

    max_row = max(cell.get("start_row_offset_idx", 0) + cell.get("row_span", 1) for cell in flat_cells)
    max_col = max(cell.get("start_col_offset_idx", 0) + cell.get("col_span", 1) for cell in flat_cells)

    cells = []
    table_page = pages[page_idx] if 0 <= page_idx < len(pages) else pages[-1]
    for cell in flat_cells:
        # Docling cells carry their own bbox dict (l/t/r/b), not prov.
        cell_bbox = _cell_bbox_to_render(cell.get("bbox"), table_page)
        cells.append(
            RenderCell(
                row_index=cell.get("start_row_offset_idx", 0),
                col_index=cell.get("start_col_offset_idx", 0),
                row_span=cell.get("row_span", 1),
                col_span=cell.get("col_span", 1),
                text=cell.get("text", "").get("markdown", cell.get("text", "")) if isinstance(cell.get("text"), dict) else str(cell.get("text", "")),
                is_header=cell.get("column_header", False),
                bbox=cell_bbox,
            ),
        )

    has_any_bbox = any(c.bbox is not None for c in cells)

    return block, RenderTable(
        block_id=block_id,
        rows=max_row,
        cols=max_col,
        cells=cells,
    ), has_any_bbox


def _picture_to_block_and_figure(
    picture_item: dict, pages: list[RenderPage],
) -> tuple[RenderBlock | None, RenderFigure | None]:
    prov = picture_item.get("prov", [])
    page_idx, bbox = _get_page_for_block(prov, pages)

    block_id = str(picture_item.get("self_ref", picture_item.get("obj_id", "")))
    if not block_id:
        block_id = f"fig_{id(picture_item)}"

    text = picture_item.get("text", "")
    block = RenderBlock(
        id=block_id,
        block_type="figure",
        text=text[:200] if text else "",
        bbox=bbox,
        page_index=page_idx,
    )

    figure = RenderFigure(
        block_id=block_id,
        image_storage_key=None,
        description=text if text else None,
    )

    return block, figure


def _resolve_ref(ref: dict | str, raw_json: dict) -> str | None:
    if isinstance(ref, str):
        return ref
    ref_id = ref.get("$ref", "")
    if ref_id:
        return str(ref_id)
    return None

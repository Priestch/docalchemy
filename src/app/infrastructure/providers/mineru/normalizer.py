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
    "text": "paragraph",
    "heading": "heading",
    "title": "heading",
    "section_header": "heading",
    "table": "table",
    "image": "figure",
    "picture": "figure",
    "figure": "figure",
    "list": "list_item",
    "list_item": "list_item",
    "caption": "caption",
    "formula": "formula",
    "page_header": "page_header",
    "page_footer": "page_footer",
    "code": "code",
    "footnote": "footnote",
}


def mineru_raw_to_render_document(
    raw_json: dict | list,
    provider_metadata: dict,
) -> RenderDocument:
    if isinstance(raw_json, list):
        raw_dict = _list_to_pdf_info_dict(raw_json)
    else:
        raw_dict = raw_json

    pdf_info = raw_dict.get("pdf_info") or raw_dict.get("page_info") or raw_dict.get("pages") or []
    if isinstance(pdf_info, dict):
        pdf_info = list(pdf_info.values())

    pages = _build_pages(pdf_info)
    block_map: dict[str, RenderBlock] = {}
    tables: list[RenderTable] = []
    figures: list[RenderFigure] = []
    reading_order: list[str] = []

    for page_data in pdf_info:
        if not isinstance(page_data, dict):
            continue
        page_idx = page_data.get("page_idx", page_data.get("page_no", page_data.get("page_index", 0)))
        page = pages[page_idx] if page_idx < len(pages) else pages[-1] if pages else _fallback_page()

        for block in (page_data.get("para_blocks") or page_data.get("preproc_blocks") or page_data.get("blocks") or []):
            if not isinstance(block, dict):
                continue
            rb = _block_to_render_block(block, page)
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

    for p in pages:
        p.children = [bid for bid, b in block_map.items() if b.page_index == p.page_index]

    return RenderDocument(
        provider_metadata=provider_metadata,
        pages=pages,
        blocks=list(block_map.values()),
        tables=tables,
        figures=figures,
        reading_order=reading_order,
    )


def _fallback_page() -> RenderPage:
    return RenderPage(page_index=0, width=612.0, height=792.0)


def _list_to_pdf_info_dict(raw_list: list) -> dict:
    return {"pdf_info": raw_list}


def _build_pages(pdf_info: list) -> list[RenderPage]:
    pages: list[RenderPage] = []
    for item in pdf_info:
        if not isinstance(item, dict):
            continue
        page_idx = item.get("page_idx", item.get("page_no", item.get("page_index", len(pages))))
        if isinstance(page_idx, str):
            page_idx = int(page_idx) if page_idx.isdigit() else len(pages)
        page_size = item.get("page_size", item.get("size", [612.0, 792.0]))
        if isinstance(page_size, (list, tuple)) and len(page_size) >= 2:
            width = float(page_size[0])
            height = float(page_size[1])
        elif isinstance(page_size, dict):
            width = float(page_size.get("width", page_size.get("w", 612.0)))
            height = float(page_size.get("height", page_size.get("h", 792.0)))
        else:
            width, height = 612.0, 792.0
        pages.append(RenderPage(page_index=max(0, page_idx), width=width, height=height))

    if not pages:
        pages.append(_fallback_page())

    pages.sort(key=lambda p: p.page_index)
    return pages


def _extract_block_text(block: dict) -> str:
    lines = block.get("lines") or block.get("text_lines") or []
    texts: list[str] = []
    for line in lines:
        if isinstance(line, str):
            texts.append(line)
            continue
        if not isinstance(line, dict):
            continue
        spans = line.get("spans") or line.get("span") or [line]
        if isinstance(spans, dict):
            spans = [spans]
        for span in spans:
            if isinstance(span, str):
                texts.append(span)
            elif isinstance(span, dict):
                content = span.get("content") or span.get("text") or span.get("markdown") or ""
                if isinstance(content, str):
                    texts.append(content)
    return "".join(texts)


def _normalize_bbox(bbox_data: list | dict | None, page: RenderPage) -> RenderBoundingBox | None:
    if bbox_data is None:
        return None

    if isinstance(bbox_data, dict):
        coords = (
            bbox_data.get("bbox")
            or bbox_data.get("coord")
            or bbox_data.get("poly")
            or bbox_data.get("bounding_box")
        )
        if coords is None:
            return None
        bbox_data = coords

    if not isinstance(bbox_data, (list, tuple)) or len(bbox_data) < 4:
        return None

    raw_x0, raw_y0, raw_x1, raw_y1 = bbox_data[:4]

    x0 = min(raw_x0, raw_x1)
    x1 = max(raw_x0, raw_x1)

    y0_raw = min(raw_y0, raw_y1)  # top edge from page top (y-down)
    y1_raw = max(raw_y0, raw_y1)  # bottom edge from page top (y-down)

    return RenderBoundingBox(
        x0=max(0.0, min(1.0, x0 / page.width if page.width else 0)),
        y0=max(0.0, min(1.0, y0_raw / page.height if page.height else 0)),
        x1=max(0.0, min(1.0, x1 / page.width if page.width else 0)),
        y1=max(0.0, min(1.0, y1_raw / page.height if page.height else 0)),
    )


def _block_to_render_block(block: dict, page: RenderPage) -> RenderBlock | None:
    block_type = TYPE_MAP.get(block.get("type", ""), "paragraph")
    bbox = _normalize_bbox(block.get("bbox") or block.get("coord") or block.get("poly") or block.get("bounding_box"), page)
    text = _extract_block_text(block)

    block_id = str(block.get("id", block.get("block_id", block.get("obj_id", ""))))
    if not block_id:
        block_id = str(block.get("index", ""))
    if not block_id or block_id.isdigit():
        block_id = f"p{page.page_index}_{block_id}" if block_id else f"p{page.page_index}_{id(block)}"

    heading_level = None
    if block_type == "heading":
        heading_level = block.get("heading_level", block.get("level", block.get("heading", 1)))
        if not isinstance(heading_level, int):
            heading_level = 1

    confidence = block.get("confidence", block.get("score"))

    return RenderBlock(
        id=block_id,
        block_type=block_type,
        text=text,
        heading_level=heading_level,
        bbox=bbox,
        page_index=page.page_index,
        confidence=confidence,
    )


def _block_to_table(block: dict, block_id: str) -> RenderTable | None:
    table_data = block.get("table") or block.get("data") or block.get("cells") or block.get("grid") or block.get("table_details")
    if table_data is None:
        return None

    if isinstance(table_data, list):
        return _list_table(table_data, block_id)

    if isinstance(table_data, dict):
        rows = table_data.get("rows", len(table_data.get("cells", [])))
        cols = table_data.get("cols", 0)
        cells = []

        for cell in table_data.get("cells", []):
            cells.append(
                RenderCell(
                    row_index=cell.get("row", cell.get("row_index", cell.get("row_idx", 0))),
                    col_index=cell.get("col", cell.get("col_index", cell.get("col_idx", 0))),
                    row_span=cell.get("row_span", cell.get("rowspan", 1)),
                    col_span=cell.get("col_span", cell.get("colspan", 1)),
                    text=str(cell.get("text", cell.get("content", ""))),
                    is_header=cell.get("is_header", cell.get("header", False)),
                )
            )

        return RenderTable(block_id=block_id, rows=rows, cols=cols, cells=cells)

    return None


def _list_table(table_data: list, block_id: str) -> RenderTable | None:
    if not table_data:
        return RenderTable(block_id=block_id, rows=0, cols=0)

    if isinstance(table_data[0], list):
        rows = len(table_data)
        cols = max(len(r) for r in table_data) if table_data else 0
        cells = []
        for ri, row in enumerate(table_data):
            for ci, cell in enumerate(row):
                cell_text = str(cell.get("text", cell.get("content", cell))) if isinstance(cell, dict) else str(cell)
                is_header = cell.get("is_header", cell.get("header", ri == 0)) if isinstance(cell, dict) else ri == 0
                cells.append(
                    RenderCell(row_index=ri, col_index=ci, text=cell_text, is_header=is_header)
                )
        return RenderTable(block_id=block_id, rows=rows, cols=cols, cells=cells)

    cells = []
    for cell in table_data:
        cells.append(
            RenderCell(
                row_index=cell.get("row", cell.get("row_index", cell.get("row_idx", 0))),
                col_index=cell.get("col", cell.get("col_index", cell.get("col_idx", 0))),
                row_span=cell.get("row_span", cell.get("rowspan", 1)),
                col_span=cell.get("col_span", cell.get("colspan", 1)),
                text=str(cell.get("text", cell.get("content", ""))),
                is_header=cell.get("is_header", cell.get("header", False)),
            )
        )

    if not cells:
        return RenderTable(block_id=block_id, rows=0, cols=0)

    max_row = max(c.row_index + c.row_span for c in cells)
    max_col = max(c.col_index + c.col_span for c in cells)
    return RenderTable(block_id=block_id, rows=max_row, cols=max_col, cells=cells)


def _block_to_figure(block: dict, block_id: str) -> RenderFigure | None:
    image_path = block.get("image_path") or block.get("image") or block.get("img_path")
    description = block.get("description") or block.get("caption") or _extract_block_text(block)
    if isinstance(description, (dict, list)):
        description = str(description)

    return RenderFigure(
        block_id=block_id,
        image_storage_key=str(image_path) if image_path else None,
        description=str(description) if description else None,
    )

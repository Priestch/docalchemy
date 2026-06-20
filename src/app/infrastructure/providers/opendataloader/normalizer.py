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
        elements = raw_json.get("elements", raw_json.get("kids", raw_json.get("content", [])))
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

    any_cell_has_bbox = False

    for idx, element in enumerate(raw_json):
        block = _element_to_block(element, idx, pages)
        if block is not None:
            blocks.append(block)
            reading_order.append(block.id)

            if block.block_type == "table":
                page = pages[block.page_index] if block.page_index < len(pages) else pages[0]
                table, has_bbox = _element_to_table(element, block.id, page)
                if table is not None:
                    tables.append(table)
                if has_bbox:
                    any_cell_has_bbox = True
            elif block.block_type == "figure":
                figure = _element_to_figure(element, block.id)
                if figure is not None:
                    figures.append(figure)

    for page in pages:
        page.children = [b.id for b in blocks if b.page_index == page.page_index]

    return RenderDocument(
        provider_metadata=provider_metadata,
        cell_bbox_mode="exact" if any_cell_has_bbox else "none",
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
        page_no = _get_page_number(el)
        if isinstance(page_no, int):
            page_indices.add(max(0, page_no - 1))

    if not page_indices:
        page_indices = {0}

    pages = []
    for pi in sorted(page_indices):
        w, h = page_dims_map.get(pi, (612.0, 792.0))
        pages.append(RenderPage(page_index=pi, width=w, height=h))
    return pages


def _get_page_number(element: dict):
    return element.get("page number", element.get("page_number", element.get("page", 1)))


def _get_page_index(element: dict) -> int:
    page_no = _get_page_number(element)
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

    bbox_data = element.get("bounding box", element.get("bounding_box", element.get("bbox")))
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


def _element_to_table(element: dict, block_id: str, page: RenderPage) -> tuple[RenderTable | None, bool]:
    # --- Path 1: Real OpenDataLoader format ---
    # Structure: element["rows"] = [{"type": "table row", "cells": [{"type": "table cell", ...}]}]
    raw_rows = element.get("rows")
    if isinstance(raw_rows, list) and raw_rows:
        num_rows = element.get("number of rows", 0)
        num_cols = element.get("number of columns", 0)
        cells: list[RenderCell] = []

        for row_obj in raw_rows:
            if not isinstance(row_obj, dict):
                continue
            for cell_obj in row_obj.get("cells", []):
                if not isinstance(cell_obj, dict):
                    continue

                row_idx = cell_obj.get("row number", 1) - 1  # 1-indexed -> 0-indexed
                col_idx = cell_obj.get("column number", 1) - 1
                row_span = cell_obj.get("row span", 1)
                col_span = cell_obj.get("column span", 1)

                # Extract text from nested kids paragraphs
                kids = cell_obj.get("kids", [])
                text_parts = []
                for kid in kids:
                    if isinstance(kid, dict):
                        text_parts.append(kid.get("content", kid.get("text", "")))
                cell_text = " ".join(str(t) for t in text_parts if t)

                # Normalize cell bbox
                cell_bbox_data = cell_obj.get("bounding box", cell_obj.get("bounding_box"))
                cell_bbox = _normalize_bbox(cell_bbox_data, page)

                # Track max row/col from actual cell data
                num_rows = max(num_rows, row_idx + row_span)
                num_cols = max(num_cols, col_idx + col_span)

                cells.append(
                    RenderCell(
                        row_index=row_idx,
                        col_index=col_idx,
                        row_span=row_span,
                        col_span=col_span,
                        text=cell_text,
                        is_header=row_idx == 0,
                        bbox=cell_bbox,
                    )
                )

        has_any_bbox = any(c.bbox is not None for c in cells)
        return RenderTable(
            block_id=block_id,
            rows=num_rows,
            cols=num_cols,
            cells=cells,
        ), has_any_bbox

    # --- Path 2: Simplified 2D grid format (used in tests / simple integrations) ---
    # Structure: element["cells"] = [[{text, is_header}, ...], ...]
    table_data = element.get("table", element.get("data", element.get("cells")))
    if not table_data:
        return RenderTable(block_id=block_id, rows=0, cols=0), False

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
        return RenderTable(block_id=block_id, rows=rows, cols=cols, cells=cells), False

    # --- Path 3: Dict with explicit rows/cols/cells ---
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
        return RenderTable(block_id=block_id, rows=rows, cols=cols, cells=cells), False

    return None, False


def _element_to_figure(element: dict, block_id: str) -> RenderFigure | None:
    description = element.get("description", element.get("caption", element.get("content", None)))
    image_key = element.get("image_path", None)
    return RenderFigure(
        block_id=block_id,
        image_storage_key=image_key,
        description=description,
    )

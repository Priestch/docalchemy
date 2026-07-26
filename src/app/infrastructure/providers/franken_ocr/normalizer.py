from __future__ import annotations

from app.infrastructure.render_document import (
    RenderBlock,
    RenderBoundingBox,
    RenderDocument,
    RenderPage,
)

# focr's `ocr <image-pdf> -o out.json` emits, per page, a `layout` list of
# detected regions: {label, boxes: [[x0,y0,x1,y1], ...]} in rasterized pixel
# space. The transcription lives separately in the top-level `markdown` field
# (stored as the raw artifact for text evaluation). For parsing/structure
# evaluation we render the regions at their true positions; text-per-box is not
# available from focr and is not needed to judge segmentation quality.

LABEL_MAP: dict[str, str] = {
    "header": "page_header",
    "footer": "page_footer",
    "page_number": "page_footer",
    "title": "heading",
    "section_header": "heading",
    "text": "paragraph",
    "paragraph": "paragraph",
    "list": "list_item",
    "list_item": "list_item",
    "caption": "caption",
    "formula": "formula",
    "equation": "formula",
    "figure": "figure",
    "image": "figure",
    "picture": "figure",
    "table": "table",
}


def franken_ocr_raw_to_render_document(
    raw_json: dict,
    provider_metadata: dict,
) -> RenderDocument:
    pages_data = raw_json.get("pages", []) if isinstance(raw_json, dict) else []

    pages: list[RenderPage] = []
    blocks: list[RenderBlock] = []
    reading_order: list[str] = []

    for page_index, page in enumerate(pages_data):
        # The viewer's annotation layer treats page dimensions as PDF points,
        # and focr's region boxes are in rasterized pixel space. The adapter
        # stamps both (from the source PDF's get_size() and the raster). Require
        # them rather than guessing — a missing dim is a bug, not an A4 page.
        point_width = float(page["page_width"])
        point_height = float(page["page_height"])
        pixel_width = float(page["pixel_width"])
        pixel_height = float(page["pixel_height"])
        pages.append(RenderPage(page_index=page_index, width=point_width, height=point_height))

        for order, region in enumerate(page.get("layout", [])):
            block_id = f"focr_p{page_index}_{order}"
            label = str(region.get("label", "text")).lower()
            block_type = LABEL_MAP.get(label, "paragraph")
            bbox = _normalized_bbox(region, pixel_width, pixel_height)

            blocks.append(
                RenderBlock(
                    id=block_id,
                    block_type=block_type,
                    text="",  # focr doesn't bind text to regions; markdown is the raw artifact
                    bbox=bbox,
                    page_index=page_index,
                    reading_order=order,
                )
            )
            pages[page_index].children.append(block_id)
            reading_order.append(block_id)

    return RenderDocument(
        provider_metadata=provider_metadata,
        pages=pages,
        blocks=blocks,
        tables=[],
        figures=[],
        reading_order=reading_order,
    )


def _normalized_bbox(region: dict, width: float, height: float) -> RenderBoundingBox | None:
    boxes = region.get("boxes") or []
    if not boxes or not width or not height:
        return None
    box = boxes[0]
    if not isinstance(box, (list, tuple)) or len(box) < 4:
        return None

    x0, y0, x1, y1 = (float(v) for v in box[:4])
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0

    clamp = lambda v: max(0.0, min(1.0, v))  # noqa: E731
    return RenderBoundingBox(
        x0=clamp(x0 / width),
        y0=clamp(y0 / height),
        x1=clamp(x1 / width),
        y1=clamp(y1 / height),
    )

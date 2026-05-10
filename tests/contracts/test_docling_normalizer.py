from __future__ import annotations

import pytest

from app.infrastructure.providers.docling.normalizer import docling_raw_to_render_document
from app.infrastructure.render_document import RenderDocument


SAMPLE_DOCLING_OUTPUT = {
    "name": "test.pdf",
    "page_count": 1,
    "pages": {
        "0": {
            "page": 0,
            "size": {"width": 612.0, "height": 792.0},
        }
    },
    "texts": [
        {
            "text": "Hello World",
            "label": "title",
            "prov": [{"page": 1, "bbox": {"l": 72, "t": 720, "r": 540, "b": 700}, "coord_origin": "BOTTOMLEFT"}],
            "self_ref": "text_0",
            "confidence": 0.99,
        },
        {
            "text": "This is a paragraph.",
            "label": "paragraph",
            "prov": [{"page": 1, "bbox": {"l": 72, "t": 680, "r": 540, "b": 660}, "coord_origin": "BOTTOMLEFT"}],
            "self_ref": "text_1",
        },
    ],
    "tables": [],
    "pictures": [],
    "main-text": {
        "children": [
            {"$ref": "text_0"},
            {"$ref": "text_1"},
        ]
    },
}


class TestDoclingNormalizer:
    def test_produces_valid_render_document(self) -> None:
        result = docling_raw_to_render_document(
            SAMPLE_DOCLING_OUTPUT,
            {"provider_id": "docling", "provider_version": "2.x"},
        )
        assert isinstance(result, RenderDocument)

    def test_has_pages(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, {})
        assert len(result.pages) == 1
        assert result.pages[0].page_index == 0
        assert result.pages[0].width == 612.0
        assert result.pages[0].height == 792.0

    def test_has_blocks(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, {})
        assert len(result.blocks) == 2

    def test_heading_block(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, {})
        heading = result.blocks[0]
        assert heading.block_type == "heading"
        assert heading.text == "Hello World"
        assert heading.heading_level == 1

    def test_paragraph_block(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, {})
        para = result.blocks[1]
        assert para.block_type == "paragraph"
        assert para.text == "This is a paragraph."

    def test_coordinates_normalized(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, {})
        for block in result.blocks:
            if block.bbox is not None:
                assert 0.0 <= block.bbox.x0 <= 1.0, f"x0 out of range: {block.bbox.x0}"
                assert 0.0 <= block.bbox.y0 <= 1.0, f"y0 out of range: {block.bbox.y0}"
                assert 0.0 <= block.bbox.x1 <= 1.0, f"x1 out of range: {block.bbox.x1}"
                assert 0.0 <= block.bbox.y1 <= 1.0, f"y1 out of range: {block.bbox.y1}"

    def test_reading_order(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, {})
        assert len(result.reading_order) == 2
        assert result.reading_order[0] == "text_0"
        assert result.reading_order[1] == "text_1"

    def test_provider_metadata(self) -> None:
        meta = {"provider_id": "docling", "provider_version": "2.14.0"}
        result = docling_raw_to_render_document(SAMPLE_DOCLING_OUTPUT, meta)
        assert result.provider_metadata["provider_id"] == "docling"

    def test_empty_input(self) -> None:
        result = docling_raw_to_render_document({}, {})
        assert isinstance(result, RenderDocument)
        assert len(result.blocks) == 0
        assert len(result.pages) >= 1  # default page

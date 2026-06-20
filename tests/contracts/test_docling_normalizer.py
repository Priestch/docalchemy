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


SAMPLE_TABLE_OUTPUT: dict = {
    "name": "table_test.pdf",
    "page_count": 1,
    "pages": {
        "0": {
            "page": 0,
            "size": {"width": 612.0, "height": 792.0},
        }
    },
    "texts": [],
    "tables": [
        {
            "text": "",
            "label": "table",
            "prov": [{"page": 1, "bbox": {"l": 72, "t": 600, "r": 540, "b": 400}, "coord_origin": "BOTTOMLEFT"}],
            "self_ref": "tbl_0",
            "data": {
                "grid": [
                    {
                        "start_row_offset_idx": 0,
                        "start_col_offset_idx": 0,
                        "row_span": 1,
                        "col_span": 1,
                        "text": "品牌",
                        "column_header": True,
                        "prov": [{"page": 1, "bbox": {"l": 72, "t": 600, "r": 200, "b": 570}, "coord_origin": "BOTTOMLEFT"}],
                    },
                    {
                        "start_row_offset_idx": 0,
                        "start_col_offset_idx": 1,
                        "row_span": 1,
                        "col_span": 1,
                        "text": "最低价",
                        "column_header": True,
                        "prov": [{"page": 1, "bbox": {"l": 200, "t": 600, "r": 320, "b": 570}, "coord_origin": "BOTTOMLEFT"}],
                    },
                    {
                        "start_row_offset_idx": 1,
                        "start_col_offset_idx": 0,
                        "row_span": 1,
                        "col_span": 1,
                        "text": "瑞幸",
                        "column_header": False,
                        "prov": [{"page": 1, "bbox": {"l": 72, "t": 570, "r": 200, "b": 540}, "coord_origin": "BOTTOMLEFT"}],
                    },
                    {
                        "start_row_offset_idx": 1,
                        "start_col_offset_idx": 1,
                        "row_span": 1,
                        "col_span": 1,
                        "text": "14",
                        "column_header": False,
                        "prov": [{"page": 1, "bbox": {"l": 200, "t": 570, "r": 320, "b": 540}, "coord_origin": "BOTTOMLEFT"}],
                    },
                ]
            },
        }
    ],
    "pictures": [],
    "main-text": {
        "children": [
            {"$ref": "tbl_0"},
        ]
    },
}


class TestDoclingTableNormalizer:
    def test_table_has_cells(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_TABLE_OUTPUT, {})
        assert len(result.tables) == 1
        table = result.tables[0]
        assert table.rows == 2
        assert table.cols == 2
        assert len(table.cells) == 4

    def test_table_cell_has_bbox(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_TABLE_OUTPUT, {})
        table = result.tables[0]
        for cell in table.cells:
            assert cell.bbox is not None, f"Cell [{cell.row_index},{cell.col_index}] missing bbox"
            assert 0.0 <= cell.bbox.x0 <= 1.0
            assert 0.0 <= cell.bbox.y0 <= 1.0
            assert 0.0 <= cell.bbox.x1 <= 1.0
            assert 0.0 <= cell.bbox.y1 <= 1.0

    def test_table_cell_preserves_text(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_TABLE_OUTPUT, {})
        table = result.tables[0]
        cell_texts = {(c.row_index, c.col_index): c.text for c in table.cells}
        assert cell_texts[(0, 0)] == "品牌"
        assert cell_texts[(0, 1)] == "最低价"
        assert cell_texts[(1, 0)] == "瑞幸"
        assert cell_texts[(1, 1)] == "14"

    def test_table_cell_preserves_header_flag(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_TABLE_OUTPUT, {})
        table = result.tables[0]
        header_cells = [c for c in table.cells if c.is_header]
        assert len(header_cells) == 2
        data_cells = [c for c in table.cells if not c.is_header]
        assert len(data_cells) == 2

    def test_table_cell_bbox_mode_is_text_extent(self) -> None:
        result = docling_raw_to_render_document(SAMPLE_TABLE_OUTPUT, {})
        assert result.cell_bbox_mode == "text_extent"

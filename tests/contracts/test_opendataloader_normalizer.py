from __future__ import annotations

import pytest

from app.infrastructure.providers.opendataloader.normalizer import opendataloader_raw_to_render_document
from app.infrastructure.render_document import RenderDocument


SAMPLE_OPENDATALOADER_OUTPUT = [
    {
        "id": "el_0",
        "type": "heading",
        "content": "Report Title",
        "page_number": 1,
        "bounding_box": [72.0, 60.0, 540.0, 80.0],
        "heading_level": 1,
    },
    {
        "id": "el_1",
        "type": "paragraph",
        "content": "First paragraph of the document.",
        "page_number": 1,
        "bounding_box": [72.0, 90.0, 540.0, 110.0],
    },
    {
        "id": "el_2",
        "type": "table",
        "content": "Data table",
        "page_number": 1,
        "bounding_box": [72.0, 120.0, 540.0, 200.0],
        "cells": [
            [{"text": "Header A", "is_header": True}, {"text": "Header B", "is_header": True}],
            [{"text": "Cell 1"}, {"text": "Cell 2"}],
        ],
    },
    {
        "id": "el_3",
        "type": "image",
        "content": "A diagram showing the architecture",
        "page_number": 1,
        "bounding_box": [72.0, 220.0, 300.0, 350.0],
    },
]


SAMPLE_PAGE_DIMENSIONS = [
    {"page_index": 0, "width": 612.0, "height": 792.0},
]


class TestOpenDataLoaderNormalizer:
    def test_produces_valid_render_document(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT,
            {"provider_id": "opendataloader"},
            page_dimensions=SAMPLE_PAGE_DIMENSIONS,
        )
        assert isinstance(result, RenderDocument)

    def test_has_pages(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        assert len(result.pages) == 1
        assert result.pages[0].width == 612.0
        assert result.pages[0].height == 792.0

    def test_has_blocks(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        assert len(result.blocks) == 4

    def test_block_types(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        types = [b.block_type for b in result.blocks]
        assert "heading" in types
        assert "paragraph" in types
        assert "table" in types
        assert "figure" in types

    def test_heading_level(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        heading = next(b for b in result.blocks if b.block_type == "heading")
        assert heading.heading_level == 1

    def test_coordinates_normalized(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        for block in result.blocks:
            if block.bbox is not None:
                assert 0.0 <= block.bbox.x0 <= 1.0, f"x0 out of range: {block.bbox.x0}"
                assert 0.0 <= block.bbox.y0 <= 1.0, f"y0 out of range: {block.bbox.y0}"
                assert 0.0 <= block.bbox.x1 <= 1.0, f"x1 out of range: {block.bbox.x1}"
                assert 0.0 <= block.bbox.y1 <= 1.0, f"y1 out of range: {block.bbox.y1}"

    def test_reading_order(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        assert len(result.reading_order) == 4

    def test_table_extraction(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        assert len(result.tables) == 1
        table = result.tables[0]
        assert table.rows == 2
        assert table.cols == 2
        assert len(table.cells) == 4

    def test_figure_extraction(self) -> None:
        result = opendataloader_raw_to_render_document(
            SAMPLE_OPENDATALOADER_OUTPUT, {}, page_dimensions=SAMPLE_PAGE_DIMENSIONS
        )
        assert len(result.figures) == 1
        figure = result.figures[0]
        assert figure.description is not None

    def test_empty_input(self) -> None:
        result = opendataloader_raw_to_render_document([], {})
        assert isinstance(result, RenderDocument)
        assert len(result.blocks) == 0

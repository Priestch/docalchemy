"""The pack normalizer: a stored normalized document becomes a RenderDocument.

The provider already did the engine-specific work — what arrives here is the
contract's Document. These tests pin the load-and-map path: kind translation,
reading order, table grids, and figure references all survive the crossing.
"""

from __future__ import annotations

from app.infrastructure.providers.pack.normalizer import pack_raw_to_render_document
from app.infrastructure.render_document import RenderDocument

SAMPLE_NORMALIZED_DOCUMENT = {
    "pages": [{"index": 0, "width": 612.0, "height": 792.0}],
    "blocks": [
        {
            "id": "heading-0",
            "kind": "heading",
            "text": "Sample Markdown",
            "order": 0,
            "page": 0,
            "level": 1,
        },
        {
            "id": "text-0",
            "kind": "text",
            "text": "A plain paragraph.",
            "order": 1,
            "page": 0,
        },
        {
            "id": "table-0",
            "kind": "table",
            "text": "",
            "order": 2,
            "page": 0,
        },
        {
            "id": "figure-0",
            "kind": "figure",
            "text": "Figure 1",
            "order": 3,
            "page": 0,
            "artifact_id": "artifacts/figure-0.png",
        },
    ],
    "tables": [
        {
            "id": "table-0",
            "rows": 2,
            "cols": 2,
            "cells": [
                {"row": 0, "col": 0, "text": "A", "is_header": True},
                {"row": 0, "col": 1, "text": "B", "is_header": True},
                {"row": 1, "col": 0, "text": "1"},
                {"row": 1, "col": 1, "text": "2"},
            ],
        }
    ],
    "markdown": "# Sample Markdown",
    "cell_bbox_mode": "none",
}

PROVIDER_METADATA = {"pack_id": "docling", "runtime_metadata": {}}


def test_normalized_document_becomes_render_document() -> None:
    render_doc = pack_raw_to_render_document(SAMPLE_NORMALIZED_DOCUMENT, PROVIDER_METADATA)

    assert isinstance(render_doc, RenderDocument)
    assert len(render_doc.blocks) == 4


def test_element_kinds_map_to_render_block_types() -> None:
    render_doc = pack_raw_to_render_document(SAMPLE_NORMALIZED_DOCUMENT, PROVIDER_METADATA)

    by_id = {block.id: block for block in render_doc.blocks}
    assert by_id["heading-0"].block_type == "heading"
    assert by_id["heading-0"].heading_level == 1
    assert by_id["text-0"].block_type == "paragraph"
    assert by_id["table-0"].block_type == "table"
    assert by_id["figure-0"].block_type == "figure"


def test_reading_order_is_preserved() -> None:
    render_doc = pack_raw_to_render_document(SAMPLE_NORMALIZED_DOCUMENT, PROVIDER_METADATA)

    assert [block.reading_order for block in render_doc.blocks] == [0, 1, 2, 3]
    assert [block.text for block in render_doc.blocks] == [
        "Sample Markdown",
        "A plain paragraph.",
        "",
        "Figure 1",
    ]


def test_table_grid_travels_with_its_block() -> None:
    render_doc = pack_raw_to_render_document(SAMPLE_NORMALIZED_DOCUMENT, PROVIDER_METADATA)

    assert len(render_doc.tables) == 1
    table = render_doc.tables[0]
    assert table.block_id == "table-0"
    assert table.rows == 2
    assert table.cols == 2
    assert [cell.text for cell in table.cells] == ["A", "B", "1", "2"]


def test_figure_block_yields_a_figure() -> None:
    render_doc = pack_raw_to_render_document(SAMPLE_NORMALIZED_DOCUMENT, PROVIDER_METADATA)

    assert len(render_doc.figures) == 1
    figure = render_doc.figures[0]
    assert figure.block_id == "figure-0"
    assert figure.image_storage_key == "artifacts/figure-0.png"
    assert figure.description == "Figure 1"


def test_unknown_kind_degrades_to_paragraph() -> None:
    document = {
        "pages": [],
        "blocks": [
            {"id": "kv-0", "kind": "key_value", "text": "key: value", "order": 0, "page": 0}
        ],
        "tables": [],
        "markdown": "",
        "cell_bbox_mode": "none",
    }

    render_doc = pack_raw_to_render_document(document, PROVIDER_METADATA)

    assert render_doc.blocks[0].block_type == "paragraph"
    assert render_doc.blocks[0].text == "key: value"

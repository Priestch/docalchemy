# RenderDocument Schema

## Purpose

`RenderDocument` is the application-owned schema consumed by the frontend viewer and comparison UI. It is the only schema the frontend may consume. The frontend must never receive provider-native output directly.

## Coordinate System

All bounding box coordinates use **normalized `[0, 1]` range** relative to page dimensions, with **top-left origin**.

Providers (Docling, OpenDataLoader) use BOTTOMLEFT origin in PDF points. Normalization converts via:

```
y0_normalized = (page_height - y0_raw) / page_height
y1_normalized = (page_height - y1_raw) / page_height
x0_normalized = x0_raw / page_width
x1_normalized = x1_raw / page_width
```

Page dimensions are stored in PDF points (1 point = 1/72 inch) for aspect ratio computation.

## Schema Definition

### RenderDocument

The top-level container for one provider's normalized analysis result.

```json
{
  "provider_metadata": {
    "provider_id": "docling",
    "provider_version": "2.14.0",
    "raw_artifact_storage_key": "ab/cdef...json",
    "normalized_at": "2024-12-31T12:00:00Z"
  },
  "pages": [RenderPage],
  "blocks": [RenderBlock],
  "tables": [RenderTable],
  "figures": [RenderFigure],
  "reading_order": ["block_id_1", "block_id_2", "..."]
}
```

### RenderPage

Represents one page of the source document.

```json
{
  "page_index": 0,
  "width": 612.0,
  "height": 792.0,
  "children": ["block_id_1", "block_id_2"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `page_index` | `int` | 0-based page index |
| `width` | `float` | Page width in PDF points |
| `height` | `float` | Page height in PDF points |
| `children` | `list[str]` | Ordered block IDs on this page |

### RenderBlock

A logical content block within a page.

```json
{
  "id": "blk_001",
  "block_type": "paragraph",
  "text": "The quick brown fox jumps over the lazy dog.",
  "heading_level": null,
  "bbox": [0.1, 0.2, 0.9, 0.3],
  "page_index": 0,
  "reading_order": 1,
  "confidence": 0.95,
  "children": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique block identifier within this RenderDocument |
| `block_type` | `str` | Block type enum (see below) |
| `text` | `str` | Plain text content |
| `heading_level` | `int \| null` | 1-6 for heading blocks, null otherwise |
| `bbox` | `list[float] \| null` | Normalized bounding box `[x0, y0, x1, y1]`, null if unavailable |
| `page_index` | `int` | 0-based page index |
| `reading_order` | `int` | Position in reading sequence |
| `confidence` | `float \| null` | Provider confidence score 0-1, null if unavailable |
| `children` | `list[str]` | Child block IDs for nested structures |

**Block types:**

| Type | Description |
|------|-------------|
| `paragraph` | Body text paragraph |
| `heading` | Section heading (check `heading_level`) |
| `list_item` | Ordered or unordered list item |
| `table` | Table (see `RenderTable` for structure) |
| `figure` | Image or figure (see `RenderFigure` for details) |
| `caption` | Figure or table caption |
| `page_header` | Running page header |
| `page_footer` | Running page footer |
| `formula` | Mathematical formula (LaTeX in `text`) |
| `key_value_area` | Form-like key-value region |
| `code` | Source code block |
| `footnote` | Footnote text |
| `toc` | Table of contents entry |

### RenderTable

Structured table data associated with a table block.

```json
{
  "block_id": "blk_010",
  "rows": 3,
  "cols": 2,
  "cells": [RenderCell]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `block_id` | `str` | References the parent `RenderBlock` with `block_type: "table"` |
| `rows` | `int` | Number of rows |
| `cols` | `int` | Number of columns |
| `cells` | `list[RenderCell]` | All cells |

### RenderCell

A single table cell.

```json
{
  "row_index": 0,
  "col_index": 0,
  "row_span": 1,
  "col_span": 1,
  "text": "Header 1",
  "bbox": [0.1, 0.5, 0.3, 0.6],
  "is_header": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `row_index` | `int` | 0-based row position |
| `col_index` | `int` | 0-based column position |
| `row_span` | `int` | Number of rows this cell spans |
| `col_span` | `int` | Number of columns this cell spans |
| `text` | `str` | Cell text content |
| `bbox` | `list[float] \| null` | Normalized bounding box |
| `is_header` | `bool` | Whether this cell is a column header |

### RenderFigure

Figure metadata associated with a figure block.

```json
{
  "block_id": "blk_015",
  "image_storage_key": "ab/figure_hash.png",
  "description": "A bar chart showing quarterly revenue"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `block_id` | `str` | References the parent `RenderBlock` with `block_type: "figure"` |
| `image_storage_key` | `str \| null` | Storage key for extracted image file |
| `description` | `str \| null` | AI-generated or caption text description |

## Reading Order

The root-level `reading_order` field is an ordered list of block IDs representing the intended reading sequence across all pages.

Each `RenderBlock` also carries a `reading_order` integer. These are consistent: the Nth element of the root `reading_order` array has `reading_order == N`.

## Provider Metadata

The `provider_metadata` object carries provenance information:

| Field | Type | Description |
|-------|------|-------------|
| `provider_id` | `str` | Which provider produced this result |
| `provider_version` | `str` | Provider software version |
| `raw_artifact_storage_key` | `str` | Key to the raw provider output in artifact storage |
| `normalized_at` | `str` | ISO 8601 timestamp of normalization |

## Pydantic Model

The canonical implementation is in `src/app/infrastructure/render_document.py` as Pydantic v2 models. The JSON schema above is the authoritative contract; the Pydantic model is its runtime representation.

## Invariants

1. Every block ID referenced in `pages[].children`, `tables[].block_id`, `figures[].block_id`, `blocks[].children`, and `reading_order` must exist in the `blocks` array.
2. All bounding box coordinates must be in `[0, 1]` range (or null).
3. `reading_order` values must be unique within a RenderDocument and form a contiguous sequence starting from 0.
4. `page_index` values must be contiguous starting from 0.
5. Table cells must not exceed `rows * cols` in count.

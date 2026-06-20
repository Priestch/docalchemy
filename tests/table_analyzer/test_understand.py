from __future__ import annotations

import pytest

from table_analyzer.models import (
    AggregateType,
    DataType,
    RawCell,
    RawTable,
    TablePattern,
    TableType,
    UnitSource,
)
from table_analyzer.understand import understand_table


# ── Test 1: Revenue by Region (row table, time series) ─────────────────────


def test_revenue_by_region(revenue_by_region):
    result = understand_table(revenue_by_region)

    # Pattern
    assert result.table_pattern == TablePattern.ROW
    assert result.table_type == TableType.TIME_SERIES

    # Headers
    assert result.header_row_count == 1
    assert result.header_col_count == 1
    assert len(result.column_headers) == 5
    assert result.column_headers[0].text == "Region"
    assert result.column_headers[1].text == "Q1 2024"

    # Temporal
    assert result.temporal_axis == "columns"
    assert len(result.temporal_values) == 3
    assert result.temporal_values[0].quarter == 1
    assert result.temporal_values[0].year == 2024

    # Unit
    assert result.default_unit == "Millions USD"
    assert result.unit_source == UnitSource.CAPTION

    # Aggregate
    assert len(result.aggregate_rows) == 1
    assert result.aggregate_rows[0].index == 4
    assert result.aggregate_rows[0].aggregate_type == AggregateType.SUM

    # Data area
    assert result.data_start_row == 1
    assert result.data_start_col == 1

    # Schema fingerprint should be non-empty
    assert result.schema_fingerprint != ""

    assert result.parse_confidence > 0


# ── Test 2: Product Specs (form / key-value) ───────────────────────────────


def test_product_specs(product_specs):
    result = understand_table(product_specs)

    # Pattern
    assert result.table_pattern == TablePattern.FORM
    assert result.table_type == TableType.PARAMETER_SPEC

    # Headers
    assert result.header_row_count == 1
    assert result.header_col_count == 0

    # Columns
    assert len(result.columns) == 2
    assert result.columns[0].name == "Parameter"
    assert result.columns[0].data_type == DataType.CATEGORICAL
    assert result.columns[1].name == "Value"

    # Data area
    assert result.data_start_row == 1

    # No aggregates in a form table
    assert len(result.aggregate_rows) == 0

    assert result.parse_confidence > 0


# ── Test 3: Confusion Matrix (sparse / diagonal) ───────────────────────────


def test_confusion_matrix(confusion_matrix):
    result = understand_table(confusion_matrix)

    # Pattern
    assert result.table_pattern == TablePattern.SPARSE

    # Headers: both row and column headers present
    assert result.header_row_count == 1
    assert result.header_col_count == 1

    # Same labels on rows and columns
    col_header_texts = [h.text for h in result.column_headers if h.text]
    row_header_texts = [h.text for h in result.row_headers if h.text]
    assert sorted(col_header_texts) == sorted(row_header_texts)

    assert result.parse_confidence > 0


# ── Test 4: Multi-level Header Table ───────────────────────────────────────


def test_revenue_multi_header(revenue_multi_header):
    result = understand_table(revenue_multi_header)

    # Pattern
    assert result.table_pattern == TablePattern.MULTI_HEADER

    # Two header rows
    assert result.header_row_count == 2
    assert result.header_col_count == 1

    # Top-level headers should include "Revenue" and "Expenses" with spans
    top_headers = [h for h in result.column_headers if h.level == 0 and h.text]
    top_texts = [h.text for h in top_headers]
    assert "Revenue" in top_texts
    assert "Expenses" in top_texts

    # "Revenue" header should span 3 columns
    revenue_header = next(h for h in top_headers if h.text == "Revenue")
    assert revenue_header.col_span == 3

    assert result.parse_confidence > 0


# ── Test 5: Hierarchical Table ─────────────────────────────────────────────


def test_org_hierarchy(org_hierarchy):
    result = understand_table(org_hierarchy)

    # Pattern
    assert result.table_pattern == TablePattern.HIERARCHICAL

    # Headers
    assert result.header_row_count == 1
    assert result.header_col_count == 1

    # Rows should have level info: parents at level 0, children at level 1
    rows = result.rows
    eng_row = next(r for r in rows if r.header_value and "Engineering" in r.header_value and r.level == 0)
    assert eng_row is not None

    frontend_row = next(r for r in rows if r.header_value and "Frontend" in r.header_value.strip())
    assert frontend_row.level == 1
    assert frontend_row.parent == "Engineering"

    assert result.parse_confidence > 0


# ── Test 6: Compound / Stacked Table ───────────────────────────────────────


def test_compound_table(compound_table):
    result = understand_table(compound_table)

    # Pattern
    assert result.table_pattern == TablePattern.STACKED

    # Compound detection
    assert result.is_compound is True
    assert len(result.sub_tables) == 2

    # Sub-table 0: Revenue by Region
    sub0 = result.sub_tables[0]
    assert sub0.caption == "Revenue by Region"
    assert sub0.columns[0].name == "Region"

    # Sub-table 1: Revenue by Product
    sub1 = result.sub_tables[1]
    assert sub1.caption == "Revenue by Product"
    assert sub1.columns[0].name == "Product"

    assert result.parse_confidence > 0


# ── Test 7: Financials with Totals ─────────────────────────────────────────


def test_financials_with_totals(financials_with_totals):
    result = understand_table(financials_with_totals)

    # Should detect all three aggregate rows
    assert len(result.aggregate_rows) == 3

    # First subtotal (row 3): sums of rows 1-2
    subtotal1 = next(a for a in result.aggregate_rows if a.index == 3)
    assert subtotal1.aggregate_type == AggregateType.SUM

    # Second subtotal (row 6): sums of rows 4-5
    subtotal2 = next(a for a in result.aggregate_rows if a.index == 6)
    assert subtotal2.aggregate_type == AggregateType.SUM

    # Grand total (row 7): sum of subtotals
    grand_total = next(a for a in result.aggregate_rows if a.index == 7)
    assert grand_total.aggregate_type == AggregateType.SUM

    assert result.parse_confidence > 0


# ── Test 8: Repeated Table Instance ────────────────────────────────────────


def test_regional_revenue_apac(regional_revenue_apac):
    result = understand_table(regional_revenue_apac)

    # Pattern
    assert result.table_pattern == TablePattern.ROW
    assert result.table_type == TableType.TIME_SERIES

    # Temporal
    assert result.temporal_axis == "columns"

    # Instance context from caption "APAC Revenue by Quarter"
    assert result.instance_context is not None
    assert result.instance_context.dimension == "Region"
    assert result.instance_context.value == "APAC"
    assert result.instance_context.source == "caption"

    # Fingerprint should be stable (same schema = same fingerprint)
    assert result.schema_fingerprint != ""

    assert result.parse_confidence > 0


# ── Test 9: Annotated Table ────────────────────────────────────────────────


def test_annotated_table(annotated_table):
    result = understand_table(annotated_table)

    # Should detect all 3 annotations
    assert len(result.annotations) == 3

    # APAC cell: "95*" with footnote about restatement
    apac_ann = next(a for a in result.annotations if a.row == 1 and a.col == 1)
    assert apac_ann.symbol == "*"
    assert apac_ann.cell_text == "95*"
    assert "Restated" in apac_ann.footnote_text or "restated" in apac_ann.footnote_text

    # EMEA cell: "92**"
    emea_ann = next(a for a in result.annotations if a.row == 2 and a.col == 1)
    assert emea_ann.symbol == "**"

    # US cell: "225†"
    us_ann = next(a for a in result.annotations if a.row == 3 and a.col == 1)
    assert us_ann.symbol == "†"

    assert result.parse_confidence > 0


# ── Test 10: Transposed Metrics ────────────────────────────────────────────


def test_transposed_metrics(transposed_metrics):
    result = understand_table(transposed_metrics)

    # Pattern: row headers contain metric names, column headers contain time
    assert result.table_pattern == TablePattern.TRANSPOSED

    # Temporal: columns are temporal
    assert result.temporal_axis == "columns"
    assert len(result.temporal_values) == 3

    # Row headers should be metric names
    row_header_texts = [h.text for h in result.row_headers]
    assert "Revenue" in row_header_texts
    assert "Expenses" in row_header_texts
    assert "Profit" in row_header_texts
    assert "Margin" in row_header_texts

    assert result.parse_confidence > 0


# ── Test 11: Missing values ────────────────────────────────────────────────


def test_table_with_missing_values(table_with_missing_values):
    result = understand_table(table_with_missing_values)

    # Should not crash and should produce a valid result
    assert result.table_pattern == TablePattern.ROW
    assert result.header_row_count == 1

    # N/A, ---, TBD, empty cells should be classified as EMPTY, not break anything
    assert result.parse_confidence > 0

    # Columns should still have correct types despite missing data
    sales_col = next(c for c in result.columns if c.name == "Q1")
    assert sales_col.data_type == DataType.NUMERIC


# ── Test 12: Accounting format ─────────────────────────────────────────────


def test_table_accounting_format(table_accounting_format):
    result = understand_table(table_accounting_format)

    assert result.table_pattern == TablePattern.ROW
    assert result.header_row_count == 1

    # Parenthesized negatives should be classified as numeric
    from table_analyzer.grid import classify_cell_type, parse_numeric

    assert classify_cell_type("(12,000)") == DataType.NUMERIC
    assert parse_numeric("(12,000)") == -12000.0
    assert parse_numeric("(3,500)") == -3500.0

    # All data columns should be numeric
    data_cols = [c for c in result.columns if c.data_type == DataType.NUMERIC]
    assert len(data_cols) >= 3

    assert result.parse_confidence > 0


# ── Test 13: Messy formatting ──────────────────────────────────────────────


def test_table_messy_formatting(table_messy_formatting):
    result = understand_table(table_messy_formatting)

    assert result.table_pattern == TablePattern.ROW
    assert result.header_row_count == 1

    from table_analyzer.grid import classify_cell_type, parse_numeric

    # Various number formats should be classified as numeric
    assert classify_cell_type("$1,234") == DataType.NUMERIC
    assert classify_cell_type("USD 890") == DataType.NUMERIC
    assert classify_cell_type("2456K") == DataType.NUMERIC
    assert classify_cell_type("8.3 pct") == DataType.NUMERIC
    assert classify_cell_type("-3.1percent") == DataType.NUMERIC

    # Parsing should extract correct values
    assert parse_numeric("$1,234") == 1234.0
    assert parse_numeric("USD 890") == 890.0
    assert parse_numeric("2456K") == 2456000.0

    assert result.parse_confidence > 0


# ── Test 14: Single column table ───────────────────────────────────────────


def test_single_column_table(single_column_table):
    result = understand_table(single_column_table)

    # Should handle single column without crashing
    assert result.parse_confidence > 0
    assert result.raw.num_rows == 4
    # Single-column table should not be detected as compound
    assert result.is_compound is False


# ── Test 15: Multi row+column header ───────────────────────────────────────


def test_table_with_multi_row_col_header(table_with_multi_row_col_header):
    result = understand_table(table_with_multi_row_col_header)

    # Should detect 2 row header columns (Category, Sub)
    assert result.header_col_count == 2
    assert result.header_row_count == 1

    # Data area should start at column 2
    assert result.data_start_col == 2

    assert result.parse_confidence > 0


# ── Edge Case Tests ────────────────────────────────────────────────────────


def test_empty_table():
    """Table with zero rows should return a minimal result."""
    raw = RawTable(num_rows=0, num_cols=0)
    result = understand_table(raw)
    assert result.table_pattern == TablePattern.GENERAL
    assert result.parse_confidence == 0.0


def test_single_row_table():
    """Table with one row should return a minimal result."""
    raw = RawTable(
        num_rows=1,
        num_cols=3,
        cells=[
            RawCell(row=0, col=0, text="A"),
            RawCell(row=0, col=1, text="B"),
            RawCell(row=0, col=2, text="C"),
        ],
    )
    result = understand_table(raw)
    assert result.parse_confidence > 0
    assert result.header_row_count == 1


# ── Test 16: Side-by-side stacked Chinese car data ─────────────────────────


def test_car_suspension_table(car_suspension_table):
    result = understand_table(car_suspension_table)

    # Should detect as compound (stacked)
    assert result.is_compound is True
    assert result.table_pattern == TablePattern.STACKED

    # Should have 4 sub-tables: 2 sections × 2 side-by-side groups
    assert len(result.sub_tables) == 4

    # First two sub-tables belong to "半自动悬架"
    assert result.sub_tables[0].caption is not None
    assert "半自动悬架" in result.sub_tables[0].caption
    assert result.sub_tables[1].caption is not None
    assert "半自动悬架" in result.sub_tables[1].caption

    # Last two sub-tables belong to "空气悬架"
    assert result.sub_tables[2].caption is not None
    assert "空气悬架" in result.sub_tables[2].caption
    assert result.sub_tables[3].caption is not None
    assert "空气悬架" in result.sub_tables[3].caption

    # Each sub-table should have 4 columns: 车系, 品牌, 车型, 价格
    for sub in result.sub_tables:
        assert len(sub.columns) == 4
        col_names = [c.name for c in sub.columns]
        assert "车系" in col_names
        assert "品牌" in col_names
        assert "车型" in col_names
        assert "价格" in col_names

    assert result.parse_confidence > 0


# ── Test 17: Chinese temporal headers (market share) ───────────────────────


def test_market_share_chinese(market_share_chinese):
    result = understand_table(market_share_chinese)

    # Pattern and type
    assert result.table_pattern == TablePattern.ROW
    assert result.table_type == TableType.TIME_SERIES

    # Temporal detection
    assert result.temporal_axis == "columns"
    assert len(result.temporal_values) == 2

    # 2021年 → year=2021
    tp1 = result.temporal_values[0]
    assert tp1.raw == "2021年"
    assert tp1.year == 2021
    assert tp1.period == "year"

    # 2022年1-5月 → year=2022, month=1, period=month_range
    tp2 = result.temporal_values[1]
    assert tp2.raw == "2022年1-5月"
    assert tp2.year == 2022
    assert tp2.month == 1
    assert tp2.period == "month_range"

    # Headers
    assert result.header_row_count == 1
    assert result.header_col_count == 1

    # Columns: col 0 is empty (skipped), so columns[0] = col 1, columns[1] = col 2
    assert len(result.columns) == 2
    col_names = [c.name for c in result.columns]
    assert "2021年" in col_names
    assert "2022年1-5月" in col_names

    # Row headers should include company names
    row_header_texts = [h.text for h in result.row_headers]
    assert "博世" in row_header_texts
    assert "同驭" in row_header_texts

    assert result.parse_confidence > 0

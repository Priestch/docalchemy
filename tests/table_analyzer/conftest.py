from __future__ import annotations

import pytest

from table_analyzer.models import RawCell, RawTable


# ── Fixture 1: Row table with time series ──────────────────────────────────
# Standard financial table: headers on top, temporal columns, unit in caption.


@pytest.fixture
def revenue_by_region() -> RawTable:
    """
    | Region   | Q1 2024 | Q2 2024 | Q3 2024 | YoY Change |
    |----------|---------|---------|---------|------------|
    | APAC     | 100     | 120     | 95      | -8.2%      |
    | EMEA     | 85      | 90      | 92      | +5.1%      |
    | Americas | 200     | 210     | 225     | +9.8%      |
    | Total    | 385     | 420     | 412     | +3.5%      |

    Caption: "Table 3: Quarterly Revenue by Region (Millions USD)"
    """
    return RawTable(
        caption="Table 3: Quarterly Revenue by Region (Millions USD)",
        num_rows=5,
        num_cols=5,
        cells=[
            # Row 0: column headers
            RawCell(row=0, col=0, text="Region"),
            RawCell(row=0, col=1, text="Q1 2024"),
            RawCell(row=0, col=2, text="Q2 2024"),
            RawCell(row=0, col=3, text="Q3 2024"),
            RawCell(row=0, col=4, text="YoY Change"),
            # Row 1: APAC
            RawCell(row=1, col=0, text="APAC"),
            RawCell(row=1, col=1, text="100"),
            RawCell(row=1, col=2, text="120"),
            RawCell(row=1, col=3, text="95"),
            RawCell(row=1, col=4, text="-8.2%"),
            # Row 2: EMEA
            RawCell(row=2, col=0, text="EMEA"),
            RawCell(row=2, col=1, text="85"),
            RawCell(row=2, col=2, text="90"),
            RawCell(row=2, col=3, text="92"),
            RawCell(row=2, col=4, text="+5.1%"),
            # Row 3: Americas
            RawCell(row=3, col=0, text="Americas"),
            RawCell(row=3, col=1, text="200"),
            RawCell(row=3, col=2, text="210"),
            RawCell(row=3, col=3, text="225"),
            RawCell(row=3, col=4, text="+9.8%"),
            # Row 4: Total (aggregate)
            RawCell(row=4, col=0, text="Total"),
            RawCell(row=4, col=1, text="385"),
            RawCell(row=4, col=2, text="420"),
            RawCell(row=4, col=3, text="412"),
            RawCell(row=4, col=4, text="+3.5%"),
        ],
        page_number=5,
        section_path=["3", "3.1", "Financial Results"],
    )


# ── Fixture 2: Form / key-value table ──────────────────────────────────────
# Model configuration: parameter name | value, no relationships between rows.


@pytest.fixture
def product_specs() -> RawTable:
    """
    | Parameter        | Value    |
    |------------------|----------|
    | Model            | GPT-4    |
    | Temperature      | 0.7      |
    | Max Tokens       | 4096     |
    | Top P            | 0.9      |
    | Frequency Penalty| 0.0      |
    """
    return RawTable(
        caption="Table 1: Model Configuration",
        num_rows=6,
        num_cols=2,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text="Parameter"),
            RawCell(row=0, col=1, text="Value"),
            # Row 1-5: key-value pairs
            RawCell(row=1, col=0, text="Model"),
            RawCell(row=1, col=1, text="GPT-4"),
            RawCell(row=2, col=0, text="Temperature"),
            RawCell(row=2, col=1, text="0.7"),
            RawCell(row=3, col=0, text="Max Tokens"),
            RawCell(row=3, col=1, text="4096"),
            RawCell(row=4, col=0, text="Top P"),
            RawCell(row=4, col=1, text="0.9"),
            RawCell(row=5, col=0, text="Frequency Penalty"),
            RawCell(row=5, col=1, text="0.0"),
        ],
        section_path=["4", "4.1", "Model Settings"],
    )


# ── Fixture 3: Sparse / diagonal table ─────────────────────────────────────
# Similarity matrix: same labels on rows and columns, diagonal is self-ref.


@pytest.fixture
def confusion_matrix() -> RawTable:
    """
    |       | A    | B    | C    |
    |-------|------|------|------|
    | A     | 1.0  | 0.85 | 0.72 |
    | B     | 0.85 | 1.0  | 0.91 |
    | C     | 0.72 | 0.91 | 1.0  |
    """
    return RawTable(
        caption="Table 5: Similarity Matrix",
        num_rows=4,
        num_cols=4,
        cells=[
            # Row 0: column headers
            RawCell(row=0, col=0, text=""),
            RawCell(row=0, col=1, text="A"),
            RawCell(row=0, col=2, text="B"),
            RawCell(row=0, col=3, text="C"),
            # Row 1: A
            RawCell(row=1, col=0, text="A"),
            RawCell(row=1, col=1, text="1.0"),
            RawCell(row=1, col=2, text="0.85"),
            RawCell(row=1, col=3, text="0.72"),
            # Row 2: B
            RawCell(row=2, col=0, text="B"),
            RawCell(row=2, col=1, text="0.85"),
            RawCell(row=2, col=2, text="1.0"),
            RawCell(row=2, col=3, text="0.91"),
            # Row 3: C
            RawCell(row=3, col=0, text="C"),
            RawCell(row=3, col=1, text="0.72"),
            RawCell(row=3, col=2, text="0.91"),
            RawCell(row=3, col=3, text="1.0"),
        ],
        section_path=["5", "5.2", "Similarity Analysis"],
    )


# ── Fixture 4: Multi-level header table ────────────────────────────────────
# Grouped columns: Revenue and Expenses each have Q1-Q3 sub-columns.


@pytest.fixture
def revenue_multi_header() -> RawTable:
    """
    |           | Revenue           | Expenses          |
    | Region    | Q1   | Q2   | Q3  | Q1   | Q2   | Q3  |
    |-----------|------|------|-----|------|------|-----|
    | APAC      | 100  | 120  | 95  | 80   | 85   | 90  |
    | EMEA      | 85   | 90   | 92  | 70   | 72   | 75  |
    """
    return RawTable(
        caption="Table 2: Revenue and Expenses by Region",
        num_rows=4,
        num_cols=7,
        cells=[
            # Row 0: top-level group headers (merged cells)
            RawCell(row=0, col=0, text=""),
            RawCell(row=0, col=1, text="Revenue", col_span=3),
            RawCell(row=0, col=2, text=""),  # covered by merge
            RawCell(row=0, col=3, text=""),  # covered by merge
            RawCell(row=0, col=4, text="Expenses", col_span=3),
            RawCell(row=0, col=5, text=""),  # covered by merge
            RawCell(row=0, col=6, text=""),  # covered by merge
            # Row 1: sub-column headers
            RawCell(row=1, col=0, text="Region"),
            RawCell(row=1, col=1, text="Q1"),
            RawCell(row=1, col=2, text="Q2"),
            RawCell(row=1, col=3, text="Q3"),
            RawCell(row=1, col=4, text="Q1"),
            RawCell(row=1, col=5, text="Q2"),
            RawCell(row=1, col=6, text="Q3"),
            # Row 2: APAC data
            RawCell(row=2, col=0, text="APAC"),
            RawCell(row=2, col=1, text="100"),
            RawCell(row=2, col=2, text="120"),
            RawCell(row=2, col=3, text="95"),
            RawCell(row=2, col=4, text="80"),
            RawCell(row=2, col=5, text="85"),
            RawCell(row=2, col=6, text="90"),
            # Row 3: EMEA data
            RawCell(row=3, col=0, text="EMEA"),
            RawCell(row=3, col=1, text="85"),
            RawCell(row=3, col=2, text="90"),
            RawCell(row=3, col=3, text="92"),
            RawCell(row=3, col=4, text="70"),
            RawCell(row=3, col=5, text="72"),
            RawCell(row=3, col=6, text="75"),
        ],
        section_path=["3", "3.2", "Financial Detail"],
    )


# ── Fixture 5: Hierarchical table ──────────────────────────────────────────
# Nested rows: parent categories with indented children.


@pytest.fixture
def org_hierarchy() -> RawTable:
    """
    | Department      | Headcount | Budget   |
    |-----------------|-----------|----------|
    | Engineering     | 150       | $12M     |
    |   Frontend      | 40        | $3M      |
    |   Backend       | 60        | $5M      |
    |   DevOps        | 50        | $4M      |
    | Sales           | 80        | $8M      |
    |   Enterprise    | 30        | $5M      |
    |   SMB           | 50        | $3M      |
    """
    return RawTable(
        caption="Table 6: Department Budget Allocation",
        num_rows=8,
        num_cols=3,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text="Department"),
            RawCell(row=0, col=1, text="Headcount"),
            RawCell(row=0, col=2, text="Budget"),
            # Row 1-4: Engineering group
            RawCell(row=1, col=0, text="Engineering"),
            RawCell(row=1, col=1, text="150"),
            RawCell(row=1, col=2, text="$12M"),
            RawCell(row=2, col=0, text="  Frontend"),
            RawCell(row=2, col=1, text="40"),
            RawCell(row=2, col=2, text="$3M"),
            RawCell(row=3, col=0, text="  Backend"),
            RawCell(row=3, col=1, text="60"),
            RawCell(row=3, col=2, text="$5M"),
            RawCell(row=4, col=0, text="  DevOps"),
            RawCell(row=4, col=1, text="50"),
            RawCell(row=4, col=2, text="$4M"),
            # Row 5-7: Sales group
            RawCell(row=5, col=0, text="Sales"),
            RawCell(row=5, col=1, text="80"),
            RawCell(row=5, col=2, text="$8M"),
            RawCell(row=6, col=0, text="  Enterprise"),
            RawCell(row=6, col=1, text="30"),
            RawCell(row=6, col=2, text="$5M"),
            RawCell(row=7, col=0, text="  SMB"),
            RawCell(row=7, col=1, text="50"),
            RawCell(row=7, col=2, text="$3M"),
        ],
        section_path=["2", "2.1", "Organization"],
    )


# ── Fixture 6: Compound / stacked table ────────────────────────────────────
# Two independent sub-tables in one visual table, separated by a schema break.


@pytest.fixture
def compound_table() -> RawTable:
    """
    | Revenue by Region            |              |
    | Region  | Q1    | Q2         |              |
    | APAC    | 100   | 120        |              |
    | EMEA    | 85    | 90         |              |
    |------------------------------|              |
    | Revenue by Product           |              |
    | Product | Q1    | Q2         |              |
    | Phones  | 80    | 95         |              |
    | Laptops | 120   | 150        |              |
    """
    return RawTable(
        caption="Table 7: Revenue Summary",
        num_rows=9,
        num_cols=3,
        cells=[
            # Sub-table 1 caption row (merged)
            RawCell(row=0, col=0, text="Revenue by Region", col_span=3),
            RawCell(row=0, col=1, text=""),
            RawCell(row=0, col=2, text=""),
            # Sub-table 1 headers
            RawCell(row=1, col=0, text="Region"),
            RawCell(row=1, col=1, text="Q1"),
            RawCell(row=1, col=2, text="Q2"),
            # Sub-table 1 data
            RawCell(row=2, col=0, text="APAC"),
            RawCell(row=2, col=1, text="100"),
            RawCell(row=2, col=2, text="120"),
            RawCell(row=3, col=0, text="EMEA"),
            RawCell(row=3, col=1, text="85"),
            RawCell(row=3, col=2, text="90"),
            # Separator (empty row)
            RawCell(row=4, col=0, text=""),
            RawCell(row=4, col=1, text=""),
            RawCell(row=4, col=2, text=""),
            # Sub-table 2 caption row (merged)
            RawCell(row=5, col=0, text="Revenue by Product", col_span=3),
            RawCell(row=5, col=1, text=""),
            RawCell(row=5, col=2, text=""),
            # Sub-table 2 headers
            RawCell(row=6, col=0, text="Product"),
            RawCell(row=6, col=1, text="Q1"),
            RawCell(row=6, col=2, text="Q2"),
            # Sub-table 2 data
            RawCell(row=7, col=0, text="Phones"),
            RawCell(row=7, col=1, text="80"),
            RawCell(row=7, col=2, text="95"),
            RawCell(row=8, col=0, text="Laptops"),
            RawCell(row=8, col=1, text="120"),
            RawCell(row=8, col=2, text="150"),
        ],
        section_path=["3", "3.1", "Revenue"],
    )


# ── Fixture 7: Financials with aggregate rows ─────────────────────────────
# Multiple aggregate rows: Subtotal and Grand Total.


@pytest.fixture
def financials_with_totals() -> RawTable:
    """
    | Category       | Q1    | Q2    | Q3    |
    |----------------|-------|-------|-------|
    | Product A      | 50    | 60    | 70    |
    | Product B      | 30    | 35    | 40    |
    | Subtotal       | 80    | 95    | 110   |
    | Product C      | 20    | 25    | 30    |
    | Product D      | 10    | 15    | 20    |
    | Subtotal       | 30    | 40    | 50    |
    | Grand Total    | 110   | 135   | 160   |
    """
    return RawTable(
        caption="Table 8: Product Revenue Breakdown",
        num_rows=8,
        num_cols=4,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text="Category"),
            RawCell(row=0, col=1, text="Q1"),
            RawCell(row=0, col=2, text="Q2"),
            RawCell(row=0, col=3, text="Q3"),
            # Row 1-2: Group 1 data
            RawCell(row=1, col=0, text="Product A"),
            RawCell(row=1, col=1, text="50"),
            RawCell(row=1, col=2, text="60"),
            RawCell(row=1, col=3, text="70"),
            RawCell(row=2, col=0, text="Product B"),
            RawCell(row=2, col=1, text="30"),
            RawCell(row=2, col=2, text="35"),
            RawCell(row=2, col=3, text="40"),
            # Row 3: Subtotal 1 (50+30=80, 60+35=95, 70+40=110)
            RawCell(row=3, col=0, text="Subtotal"),
            RawCell(row=3, col=1, text="80"),
            RawCell(row=3, col=2, text="95"),
            RawCell(row=3, col=3, text="110"),
            # Row 4-5: Group 2 data
            RawCell(row=4, col=0, text="Product C"),
            RawCell(row=4, col=1, text="20"),
            RawCell(row=4, col=2, text="25"),
            RawCell(row=4, col=3, text="30"),
            RawCell(row=5, col=0, text="Product D"),
            RawCell(row=5, col=1, text="10"),
            RawCell(row=5, col=2, text="15"),
            RawCell(row=5, col=3, text="20"),
            # Row 6: Subtotal 2 (20+10=30, 25+15=40, 30+20=50)
            RawCell(row=6, col=0, text="Subtotal"),
            RawCell(row=6, col=1, text="30"),
            RawCell(row=6, col=2, text="40"),
            RawCell(row=6, col=3, text="50"),
            # Row 7: Grand Total (80+30=110, 95+40=135, 110+50=160)
            RawCell(row=7, col=0, text="Grand Total"),
            RawCell(row=7, col=1, text="110"),
            RawCell(row=7, col=2, text="135"),
            RawCell(row=7, col=3, text="160"),
        ],
        section_path=["3", "3.3", "Product Analysis"],
    )


# ── Fixture 8: Repeated table instance ─────────────────────────────────────
# One instance of a repeated pattern — "APAC" is the differentiating dimension.


@pytest.fixture
def regional_revenue_apac() -> RawTable:
    """
    | Quarter | Revenue | Growth |
    |---------|---------|--------|
    | Q1 2024 | 100     | +5.0%  |
    | Q2 2024 | 120     | +20.0% |
    | Q3 2024 | 95      | -20.8% |

    Caption: "APAC Revenue by Quarter"
    """
    return RawTable(
        caption="APAC Revenue by Quarter",
        num_rows=4,
        num_cols=3,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text="Quarter"),
            RawCell(row=0, col=1, text="Revenue"),
            RawCell(row=0, col=2, text="Growth"),
            # Row 1-3: data
            RawCell(row=1, col=0, text="Q1 2024"),
            RawCell(row=1, col=1, text="100"),
            RawCell(row=1, col=2, text="+5.0%"),
            RawCell(row=2, col=0, text="Q2 2024"),
            RawCell(row=2, col=1, text="120"),
            RawCell(row=2, col=2, text="+20.0%"),
            RawCell(row=3, col=0, text="Q3 2024"),
            RawCell(row=3, col=1, text="95"),
            RawCell(row=3, col=2, text="-20.8%"),
        ],
        section_path=["4", "4.1", "APAC"],
    )


# ── Fixture 9: Annotated table ─────────────────────────────────────────────
# Cells with superscript symbols referencing footnotes.


@pytest.fixture
def annotated_table() -> RawTable:
    """
    | Region | Revenue  | Growth   |
    |--------|----------|----------|
    | APAC   | 95*      | -8.2%    |
    | EMEA   | 92**     | +5.1%    |
    | US     | 225†     | +9.8%    |

    Footnotes:
    * Restated due to accounting change
    ** Preliminary estimate
    † Year-over-year
    """
    return RawTable(
        caption="Table 9: Regional Performance",
        num_rows=4,
        num_cols=3,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text="Region"),
            RawCell(row=0, col=1, text="Revenue"),
            RawCell(row=0, col=2, text="Growth"),
            # Row 1: APAC with annotation *
            RawCell(row=1, col=0, text="APAC"),
            RawCell(row=1, col=1, text="95*"),
            RawCell(row=1, col=2, text="-8.2%"),
            # Row 2: EMEA with annotation **
            RawCell(row=2, col=0, text="EMEA"),
            RawCell(row=2, col=1, text="92**"),
            RawCell(row=2, col=2, text="+5.1%"),
            # Row 3: US with annotation †
            RawCell(row=3, col=0, text="US"),
            RawCell(row=3, col=1, text="225†"),
            RawCell(row=3, col=2, text="+9.8%"),
        ],
        footnotes=[
            "* Restated due to accounting change",
            "** Preliminary estimate",
            "† Year-over-year",
        ],
        section_path=["3", "3.1", "Regional"],
    )


# ── Fixture 10: Transposed table ───────────────────────────────────────────
# Metrics as rows, time periods as columns — the inverse of a typical layout.


@pytest.fixture
def transposed_metrics() -> RawTable:
    """
    | Metric    | Q1 2024 | Q2 2024 | Q3 2024 |
    |-----------|---------|---------|---------|
    | Revenue   | 385     | 420     | 412     |
    | Expenses  | 300     | 310     | 325     |
    | Profit    | 85      | 110     | 87      |
    | Margin    | 22.1%   | 26.2%   | 21.1%   |
    """
    return RawTable(
        caption="Table 10: Quarterly Financial Metrics",
        num_rows=5,
        num_cols=4,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text="Metric"),
            RawCell(row=0, col=1, text="Q1 2024"),
            RawCell(row=0, col=2, text="Q2 2024"),
            RawCell(row=0, col=3, text="Q3 2024"),
            # Row 1-4: metrics as rows
            RawCell(row=1, col=0, text="Revenue"),
            RawCell(row=1, col=1, text="385"),
            RawCell(row=1, col=2, text="420"),
            RawCell(row=1, col=3, text="412"),
            RawCell(row=2, col=0, text="Expenses"),
            RawCell(row=2, col=1, text="300"),
            RawCell(row=2, col=2, text="310"),
            RawCell(row=2, col=3, text="325"),
            RawCell(row=3, col=0, text="Profit"),
            RawCell(row=3, col=1, text="85"),
            RawCell(row=3, col=2, text="110"),
            RawCell(row=3, col=3, text="87"),
            RawCell(row=4, col=0, text="Margin"),
            RawCell(row=4, col=1, text="22.1%"),
            RawCell(row=4, col=2, text="26.2%"),
            RawCell(row=4, col=3, text="21.1%"),
        ],
        section_path=["3", "3.4", "Quarterly Metrics"],
    )


# ── Fixture 11: Table with missing values ──────────────────────────────────
# Real-world data with N/A, empty cells, and dashes mixed with actual data.


@pytest.fixture
def table_with_missing_values() -> RawTable:
    """
    | Product | Q1    | Q2    | Q3    |
    |---------|-------|-------|-------|
    | Alpha   | 100   | N/A   | 120   |
    | Beta    | ---   | 85    |       |
    | Gamma   | 200   | 210   | TBD   |
    """
    return RawTable(
        caption="Table 11: Product Performance",
        num_rows=4,
        num_cols=4,
        cells=[
            RawCell(row=0, col=0, text="Product"),
            RawCell(row=0, col=1, text="Q1"),
            RawCell(row=0, col=2, text="Q2"),
            RawCell(row=0, col=3, text="Q3"),
            RawCell(row=1, col=0, text="Alpha"),
            RawCell(row=1, col=1, text="100"),
            RawCell(row=1, col=2, text="N/A"),
            RawCell(row=1, col=3, text="120"),
            RawCell(row=2, col=0, text="Beta"),
            RawCell(row=2, col=1, text="---"),
            RawCell(row=2, col=2, text="85"),
            RawCell(row=2, col=3, text=""),
            RawCell(row=3, col=0, text="Gamma"),
            RawCell(row=3, col=1, text="200"),
            RawCell(row=3, col=2, text="210"),
            RawCell(row=3, col=3, text="TBD"),
        ],
    )


# ── Fixture 12: Accounting format ──────────────────────────────────────────
# Parenthesized negatives and financial formatting.


@pytest.fixture
def table_accounting_format() -> RawTable:
    """
    | Category    | Q1      | Q2      | Q3      |
    |-------------|---------|---------|---------|
    | Revenue     | 385,000 | 420,000 | 412,000 |
    | Expenses    | 300,000 | 310,000 | 325,000 |
    | Net Income  | 85,000  | 110,000 | 87,000  |
    | Prior Year  | (12,000)| 5,000   | (3,500) |
    """
    return RawTable(
        caption="Table 12: Financial Summary (USD)",
        num_rows=5,
        num_cols=4,
        cells=[
            RawCell(row=0, col=0, text="Category"),
            RawCell(row=0, col=1, text="Q1"),
            RawCell(row=0, col=2, text="Q2"),
            RawCell(row=0, col=3, text="Q3"),
            RawCell(row=1, col=0, text="Revenue"),
            RawCell(row=1, col=1, text="385,000"),
            RawCell(row=1, col=2, text="420,000"),
            RawCell(row=1, col=3, text="412,000"),
            RawCell(row=2, col=0, text="Expenses"),
            RawCell(row=2, col=1, text="300,000"),
            RawCell(row=2, col=2, text="310,000"),
            RawCell(row=2, col=3, text="325,000"),
            RawCell(row=3, col=0, text="Net Income"),
            RawCell(row=3, col=1, text="85,000"),
            RawCell(row=3, col=2, text="110,000"),
            RawCell(row=3, col=3, text="87,000"),
            RawCell(row=4, col=0, text="Prior Year"),
            RawCell(row=4, col=1, text="(12,000)"),
            RawCell(row=4, col=2, text="5,000"),
            RawCell(row=4, col=3, text="(3,500)"),
        ],
    )


# ── Fixture 13: Messy formatting ───────────────────────────────────────────
# Inconsistent spacing, mixed number formats.


@pytest.fixture
def table_messy_formatting() -> RawTable:
    """
    | Region  | Sales    | Growth     |
    |---------|----------|------------|
    | APAC    | $1,234   | +12.5%     |
    | EMEA    | USD 890  | 8.3 pct    |
    | Americas| 2456K    | -3.1percent |
    """
    return RawTable(
        caption="Table 13: Regional Sales",
        num_rows=4,
        num_cols=3,
        cells=[
            RawCell(row=0, col=0, text="Region"),
            RawCell(row=0, col=1, text="Sales"),
            RawCell(row=0, col=2, text="Growth"),
            RawCell(row=1, col=0, text="APAC"),
            RawCell(row=1, col=1, text="$1,234"),
            RawCell(row=1, col=2, text="+12.5%"),
            RawCell(row=2, col=0, text="EMEA"),
            RawCell(row=2, col=1, text="USD 890"),
            RawCell(row=2, col=2, text="8.3 pct"),
            RawCell(row=3, col=0, text="Americas"),
            RawCell(row=3, col=1, text="2456K"),
            RawCell(row=3, col=2, text="-3.1percent"),
        ],
    )


# ── Fixture 14: Single column table ────────────────────────────────────────
# Minimal table with one column — should not crash.


@pytest.fixture
def single_column_table() -> RawTable:
    """
    | Metric      |
    |-------------|
    | Revenue     |
    | Expenses    |
    | Profit      |
    """
    return RawTable(
        caption="Table 14: Key Metrics",
        num_rows=4,
        num_cols=1,
        cells=[
            RawCell(row=0, col=0, text="Metric"),
            RawCell(row=1, col=0, text="Revenue"),
            RawCell(row=2, col=0, text="Expenses"),
            RawCell(row=3, col=0, text="Profit"),
        ],
    )


# ── Fixture 15: Multi row+column header ────────────────────────────────────
# Two row header columns: category + subcategory.


@pytest.fixture
def table_with_multi_row_col_header() -> RawTable:
    """
    | Category  | Sub      | Q1  | Q2  |
    |-----------|----------|-----|-----|
    | Hardware  | Servers  | 500 | 600 |
    | Hardware  | Storage  | 300 | 350 |
    | Software  | Licenses | 200 | 250 |
    | Software  | Support  | 100 | 120 |
    """
    return RawTable(
        caption="Table 15: Revenue by Category",
        num_rows=5,
        num_cols=4,
        cells=[
            RawCell(row=0, col=0, text="Category"),
            RawCell(row=0, col=1, text="Sub"),
            RawCell(row=0, col=2, text="Q1"),
            RawCell(row=0, col=3, text="Q2"),
            RawCell(row=1, col=0, text="Hardware"),
            RawCell(row=1, col=1, text="Servers"),
            RawCell(row=1, col=2, text="500"),
            RawCell(row=1, col=3, text="600"),
            RawCell(row=2, col=0, text="Hardware"),
            RawCell(row=2, col=1, text="Storage"),
            RawCell(row=2, col=2, text="300"),
            RawCell(row=2, col=3, text="350"),
            RawCell(row=3, col=0, text="Software"),
            RawCell(row=3, col=1, text="Licenses"),
            RawCell(row=3, col=2, text="200"),
            RawCell(row=3, col=3, text="250"),
            RawCell(row=4, col=0, text="Software"),
            RawCell(row=4, col=1, text="Support"),
            RawCell(row=4, col=2, text="100"),
            RawCell(row=4, col=3, text="120"),
        ],
    )


# ── Fixture 16: Side-by-side stacked Chinese car data ──────────────────────
# Two sections stacked vertically, each with side-by-side tables.
# Category separators: "半自动悬架 | - | ..." and "空气悬架 | - | ..."


@pytest.fixture
def car_suspension_table() -> RawTable:
    r"""
    半自动悬架 | - | - | - | - | - | - | -
    车系 | 品牌 | 车型 | 价格 | 车系 | 品牌 | 车型 | 价格
    合资 | 奥迪 | Q6  | 45.96| 合资 | 大众 | ID.4 CROZZ | 28.73
    合资 | 奥迪 | Q5 e-tron | 45.95 | 合资 | 别克 | 昂科威 | 27.99
    合资 | 宝马 | 2系 | 41.98 | 合资 | 本田 | UR-V | 27.98
    空气悬架 | - | - | - | - | - | - | -
    车系 | 品牌 | 车型 | 价格 | 车系 | 品牌 | 车型 | 价格
    进口 | 宝马 | XM | 230 | 合资 | 沃尔沃 | S90 | 45.09
    进口 | 奔驰 | G级 | 189.2 | 合资 | 沃尔沃 | XC60 | 39.69
    进口 | 迈巴赫 | S级 | 146.8 | 合资 | 宝马 | i3 | 34.99
    """
    return RawTable(
        caption="悬架类型车型对比",
        num_rows=8,
        num_cols=8,
        cells=[
            # Row 0: category separator "半自动悬架"
            RawCell(row=0, col=0, text="半自动悬架"),
            RawCell(row=0, col=1, text="-"),
            RawCell(row=0, col=2, text="-"),
            RawCell(row=0, col=3, text="-"),
            RawCell(row=0, col=4, text="-"),
            RawCell(row=0, col=5, text="-"),
            RawCell(row=0, col=6, text="-"),
            RawCell(row=0, col=7, text="-"),
            # Row 1: column headers (repeated side-by-side)
            RawCell(row=1, col=0, text="车系"),
            RawCell(row=1, col=1, text="品牌"),
            RawCell(row=1, col=2, text="车型"),
            RawCell(row=1, col=3, text="价格"),
            RawCell(row=1, col=4, text="车系"),
            RawCell(row=1, col=5, text="品牌"),
            RawCell(row=1, col=6, text="车型"),
            RawCell(row=1, col=7, text="价格"),
            # Row 2: data
            RawCell(row=2, col=0, text="合资"),
            RawCell(row=2, col=1, text="奥迪"),
            RawCell(row=2, col=2, text="Q6"),
            RawCell(row=2, col=3, text="45.96"),
            RawCell(row=2, col=4, text="合资"),
            RawCell(row=2, col=5, text="大众"),
            RawCell(row=2, col=6, text="ID.4 CROZZ"),
            RawCell(row=2, col=7, text="28.73"),
            # Row 3: data
            RawCell(row=3, col=0, text="合资"),
            RawCell(row=3, col=1, text="奥迪"),
            RawCell(row=3, col=2, text="Q5 e-tron"),
            RawCell(row=3, col=3, text="45.95"),
            RawCell(row=3, col=4, text="合资"),
            RawCell(row=3, col=5, text="别克"),
            RawCell(row=3, col=6, text="昂科威"),
            RawCell(row=3, col=7, text="27.99"),
            # Row 4: data
            RawCell(row=4, col=0, text="合资"),
            RawCell(row=4, col=1, text="宝马"),
            RawCell(row=4, col=2, text="2系"),
            RawCell(row=4, col=3, text="41.98"),
            RawCell(row=4, col=4, text="合资"),
            RawCell(row=4, col=5, text="本田"),
            RawCell(row=4, col=6, text="UR-V"),
            RawCell(row=4, col=7, text="27.98"),
            # Row 5: category separator "空气悬架"
            RawCell(row=5, col=0, text="空气悬架"),
            RawCell(row=5, col=1, text="-"),
            RawCell(row=5, col=2, text="-"),
            RawCell(row=5, col=3, text="-"),
            RawCell(row=5, col=4, text="-"),
            RawCell(row=5, col=5, text="-"),
            RawCell(row=5, col=6, text="-"),
            RawCell(row=5, col=7, text="-"),
            # Row 6: column headers (repeated)
            RawCell(row=6, col=0, text="车系"),
            RawCell(row=6, col=1, text="品牌"),
            RawCell(row=6, col=2, text="车型"),
            RawCell(row=6, col=3, text="价格"),
            RawCell(row=6, col=4, text="车系"),
            RawCell(row=6, col=5, text="品牌"),
            RawCell(row=6, col=6, text="车型"),
            RawCell(row=6, col=7, text="价格"),
            # Row 7: data
            RawCell(row=7, col=0, text="进口"),
            RawCell(row=7, col=1, text="宝马"),
            RawCell(row=7, col=2, text="XM"),
            RawCell(row=7, col=3, text="230"),
            RawCell(row=7, col=4, text="合资"),
            RawCell(row=7, col=5, text="沃尔沃"),
            RawCell(row=7, col=6, text="S90"),
            RawCell(row=7, col=7, text="45.09"),
        ],
    )


# ── Fixture 17: Chinese temporal headers (market share) ────────────────────
# Column headers are Chinese temporal: "2021年", "2022年1-5月"
# Row headers are company names. No explicit empty top-left cell.


@pytest.fixture
def market_share_chinese() -> RawTable:
    r"""
    |           | 2021年  | 2022年1-5月 |
    | 博世      | 91.5    | 89.4        |
    | 同驭      | 3.5     | 4.3         |
    | 采埃孚    | 1       | 1.5         |
    | 万都      | 0.3     | 1.3         |
    | 拿森      | 0.6     | 0.8         |
    | 其他      | 3.1     | 2.7         |
    """
    return RawTable(
        caption="市场份额占比",
        num_rows=7,
        num_cols=3,
        cells=[
            # Row 0: headers
            RawCell(row=0, col=0, text=""),
            RawCell(row=0, col=1, text="2021年"),
            RawCell(row=0, col=2, text="2022年1-5月"),
            # Row 1-6: data
            RawCell(row=1, col=0, text="博世"),
            RawCell(row=1, col=1, text="91.5"),
            RawCell(row=1, col=2, text="89.4"),
            RawCell(row=2, col=0, text="同驭"),
            RawCell(row=2, col=1, text="3.5"),
            RawCell(row=2, col=2, text="4.3"),
            RawCell(row=3, col=0, text="采埃孚"),
            RawCell(row=3, col=1, text="1"),
            RawCell(row=3, col=2, text="1.5"),
            RawCell(row=4, col=0, text="万都"),
            RawCell(row=4, col=1, text="0.3"),
            RawCell(row=4, col=2, text="1.3"),
            RawCell(row=5, col=0, text="拿森"),
            RawCell(row=5, col=1, text="0.6"),
            RawCell(row=5, col=2, text="0.8"),
            RawCell(row=6, col=0, text="其他"),
            RawCell(row=6, col=1, text="3.1"),
            RawCell(row=6, col=2, text="2.7"),
        ],
    )

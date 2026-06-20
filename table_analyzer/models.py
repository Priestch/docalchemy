from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────────


class TablePattern(str, Enum):
    ROW = "row"
    COLUMN = "column"
    MATRIX = "matrix"
    HIERARCHICAL = "hierarchical"
    MULTI_HEADER = "multi_header"
    FORM = "form"
    SPARSE = "sparse"
    STACKED = "stacked"
    SIDE_BY_SIDE = "side_by_side"
    TRANSPOSED = "transposed"
    TIMELINE = "timeline"
    IMAGE = "image"
    GENERAL = "general"


class TableType(str, Enum):
    TIME_SERIES = "time_series"
    COMPARISON = "comparison"
    CROSS_TAB = "cross_tab"
    PARAMETER_SPEC = "parameter_spec"
    HIERARCHICAL_SUMMARY = "hierarchical_summary"
    GENERAL = "general"


class DataType(str, Enum):
    NUMERIC = "numeric"
    TEMPORAL = "temporal"
    CATEGORICAL = "categorical"
    EMPTY = "empty"
    TEXT = "text"


class AggregateType(str, Enum):
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    PERCENTAGE = "percentage"


class UnitSource(str, Enum):
    FOOTNOTE = "footnote"
    COLUMN_HEADER = "column_header"
    CAPTION = "caption"
    CELL = "cell"


# ── Input Types ────────────────────────────────────────────────────────────


@dataclass
class RawCell:
    row: int
    col: int
    text: str = ""
    row_span: int = 1
    col_span: int = 1
    is_bold: bool | None = None
    is_header: bool | None = None
    background_color: str | None = None


@dataclass
class RawTable:
    cells: list[RawCell] = field(default_factory=list)
    num_rows: int = 0
    num_cols: int = 0
    caption: str | None = None
    footnotes: list[str] = field(default_factory=list)
    page_number: int | None = None
    section_path: list[str] = field(default_factory=list)


# ── Supporting Types ───────────────────────────────────────────────────────


@dataclass
class HeaderCell:
    text: str
    level: int = 0
    row_span: int = 1
    col_span: int = 1
    col_range: tuple[int, int] | None = None
    row_range: tuple[int, int] | None = None


@dataclass
class ColumnDef:
    index: int
    name: str
    data_type: DataType
    unit: str | None = None


@dataclass
class RowDef:
    index: int
    header_value: str | None = None
    data_type: DataType | None = None
    level: int = 0
    parent: str | None = None
    continuation_of: int | None = None
    sub_rows: list[RowDef] = field(default_factory=list)


@dataclass
class TimePoint:
    raw: str
    year: int | None = None
    quarter: int | None = None
    month: int | None = None
    date: str | None = None
    period: str | None = None


@dataclass
class AggregateDef:
    index: int
    aggregate_type: AggregateType
    scope: str | None = None


@dataclass
class Annotation:
    symbol: str
    row: int
    col: int
    cell_text: str
    footnote_text: str


@dataclass
class InstanceContext:
    dimension: str
    value: str
    source: str
    confidence: float


@dataclass
class SubTable:
    index: int
    caption: str | None = None
    column_headers: list[HeaderCell] = field(default_factory=list)
    row_headers: list[HeaderCell] = field(default_factory=list)
    columns: list[ColumnDef] = field(default_factory=list)
    rows: list[RowDef] = field(default_factory=list)
    data_bounds: tuple[int, int, int, int] = (0, 0, 0, 0)
    table_type: TableType = TableType.GENERAL
    aggregate_rows: list[AggregateDef] = field(default_factory=list)
    aggregate_columns: list[AggregateDef] = field(default_factory=list)


# ── Output Type ────────────────────────────────────────────────────────────


@dataclass
class SemanticTable:
    # Identity
    raw: RawTable

    # Pattern
    table_pattern: TablePattern

    # Headers
    column_headers: list[HeaderCell] = field(default_factory=list)
    row_headers: list[HeaderCell] = field(default_factory=list)
    header_row_count: int = 0
    header_col_count: int = 0

    # Schema
    columns: list[ColumnDef] = field(default_factory=list)
    rows: list[RowDef] = field(default_factory=list)

    # Data area
    data_start_row: int = 0
    data_start_col: int = 0
    data_end_row: int = 0
    data_end_col: int = 0

    # Classification
    table_type: TableType = TableType.GENERAL
    temporal_axis: str | None = None
    temporal_values: list[TimePoint] = field(default_factory=list)

    # Aggregates
    aggregate_rows: list[AggregateDef] = field(default_factory=list)
    aggregate_columns: list[AggregateDef] = field(default_factory=list)

    # Units
    default_unit: str | None = None
    column_units: dict[int, str] = field(default_factory=dict)
    unit_source: UnitSource | None = None

    # Annotations
    annotations: list[Annotation] = field(default_factory=list)

    # Repeated table awareness
    schema_fingerprint: str = ""
    instance_context: InstanceContext | None = None

    # Compound table awareness
    is_compound: bool = False
    sub_tables: list[SubTable] = field(default_factory=list)

    # Confidence
    parse_confidence: float = 0.0

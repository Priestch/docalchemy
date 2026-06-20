from __future__ import annotations

import hashlib
import re

from table_analyzer.grid import Grid, classify_cell_type, is_numeric, parse_numeric
from table_analyzer.models import (
    AggregateDef,
    AggregateType,
    Annotation,
    ColumnDef,
    DataType,
    HeaderCell,
    InstanceContext,
    RawTable,
    RowDef,
    SemanticTable,
    SubTable,
    TablePattern,
    TableType,
    TimePoint,
    UnitSource,
)


def understand_table(raw: RawTable) -> SemanticTable:
    if raw.num_rows == 0 or raw.num_cols == 0:
        return SemanticTable(raw=raw, table_pattern=TablePattern.GENERAL, parse_confidence=0.0)

    if raw.num_rows == 1:
        # Single row: treat as header-only
        columns = [
            ColumnDef(index=c, name=raw.cells[c].text if c < len(raw.cells) else "", data_type=DataType.CATEGORICAL)
            for c in range(raw.num_cols)
        ]
        return SemanticTable(
            raw=raw,
            table_pattern=TablePattern.GENERAL,
            columns=columns,
            header_row_count=1,
            parse_confidence=0.5,
        )

    grid = Grid.from_raw(raw)

    # Step 1: Detect compound table
    is_compound, sub_boundaries = _detect_compound(grid)
    if is_compound and len(sub_boundaries) >= 2:
        return _analyze_compound(raw, grid, sub_boundaries)

    # Step 2: Detect pattern
    pattern = _detect_pattern(grid)

    # Step 3: Detect headers
    header_row_count, header_col_count = _detect_headers(grid, pattern)

    # Step 4: Extract schema
    columns = _extract_columns(grid, header_row_count)
    rows = _extract_rows(grid, header_row_count, header_col_count, pattern)
    rows = _merge_continuation_rows(rows, grid, header_row_count)

    # Step 5: Detect aggregates
    aggregate_rows = _detect_aggregate_rows(grid, header_row_count, header_col_count)

    # Step 6: Classify table type
    table_type, temporal_axis, temporal_values = _classify_table_type(
        grid, columns, header_row_count, header_col_count, pattern
    )

    # Step 7: Resolve units
    default_unit, column_units, unit_source = _resolve_units(raw, grid, header_row_count)

    # Step 8: Extract annotations
    annotations = _extract_annotations(grid, raw.footnotes, header_row_count)

    # Step 9: Fingerprint
    fingerprint = _compute_fingerprint(columns, header_row_count, header_col_count)

    # Step 10: Instance context
    instance_context = _extract_instance_context(raw)

    # Data area
    data_start_row = header_row_count
    data_start_col = header_col_count
    data_end_row = raw.num_rows
    data_end_col = raw.num_cols

    # Build column headers
    column_headers = _build_column_headers(grid, header_row_count)
    row_headers = _build_row_headers(grid, header_row_count, header_col_count)

    return SemanticTable(
        raw=raw,
        table_pattern=pattern,
        column_headers=column_headers,
        row_headers=row_headers,
        header_row_count=header_row_count,
        header_col_count=header_col_count,
        columns=columns,
        rows=rows,
        data_start_row=data_start_row,
        data_start_col=data_start_col,
        data_end_row=data_end_row,
        data_end_col=data_end_col,
        table_type=table_type,
        temporal_axis=temporal_axis,
        temporal_values=temporal_values,
        aggregate_rows=aggregate_rows,
        default_unit=default_unit,
        column_units=column_units,
        unit_source=unit_source,
        annotations=annotations,
        schema_fingerprint=fingerprint,
        instance_context=instance_context,
        is_compound=False,
        parse_confidence=1.0,
    )


# ── Compound Detection ─────────────────────────────────────────────────────


def _detect_compound(grid: Grid) -> tuple[bool, list[tuple[int, int]]]:
    """Detect if the table contains multiple sub-tables separated by schema breaks."""
    boundaries: list[tuple[int, int]] = []
    current_start = 0
    i = 0

    while i < grid.num_rows:
        # Empty separator row
        if _is_empty_row(grid, i):
            if i > current_start:
                boundaries.append((current_start, i))
            current_start = i + 1
            i += 1
            continue

        # Category separator row: "半自动悬架 | - | - | ..."
        if _is_category_separator_row(grid, i) and i > current_start + 1:
            boundaries.append((current_start, i))
            # Include the separator row in the next sub-table as its caption
            current_start = i
            i += 1
            continue

        # Caption row (merged cell spanning full width with text)
        if _is_caption_row(grid, i) and i > current_start + 1:
            boundaries.append((current_start, i))
            # Include the caption row in the next sub-table
            current_start = i
            i += 1
            continue

        if i > current_start + 2 and _is_schema_break(grid, current_start, i):
            boundaries.append((current_start, i))
            current_start = i
            i += 1
            continue

        i += 1

    if current_start < grid.num_rows:
        boundaries.append((current_start, grid.num_rows))

    if len(boundaries) <= 1:
        return False, boundaries

    # Check that sub-tables have genuinely different schemas
    # Compare both column types and header text
    schemas = []
    for start, end in boundaries:
        col_count = _count_non_empty_cols(grid, start, end)
        first_data = start
        if _is_caption_row(grid, start) or _is_category_separator_row(grid, start):
            first_data = start + 1
        first_row_types = [classify_cell_type(grid.text(first_data, c)) for c in range(grid.num_cols)]
        # Include the actual header text to distinguish "Region" from "Product"
        first_row_texts = tuple(grid.text(first_data, c).strip().lower() for c in range(grid.num_cols))
        schemas.append((col_count, tuple(first_row_types), first_row_texts))

    # If types differ, it's compound
    type_schemas = [(s[0], s[1]) for s in schemas]
    if len(set(type_schemas)) > 1:
        return True, boundaries

    # Same types but different header text means different sub-tables
    if len(set(schemas)) > 1:
        return True, boundaries

    # Same schema but separated by category headers → still compound
    if any(_is_category_separator_row(grid, start) for start, _ in boundaries):
        return True, boundaries

    return False, boundaries


def _is_empty_row(grid: Grid, row: int) -> bool:
    texts = [grid.text(row, c).strip() for c in range(grid.num_cols)]
    return all(not t for t in texts)


def _is_category_separator_row(grid: Grid, row: int) -> bool:
    """Detect rows like: '半自动悬架 | - | - | - | - | - | - | -'

    Col 0 has text, remaining cols are empty or dash-like placeholders.
    These are section dividers in compound tables.
    """
    if grid.num_cols < 2:
        return False
    first = grid.text(row, 0).strip()
    if not first or classify_cell_type(first) != DataType.CATEGORICAL:
        return False
    # All remaining cells must be empty or "-"
    for c in range(1, grid.num_cols):
        t = grid.text(row, c).strip()
        if t and t not in ("-", "—", "–", "─"):
            return False
    return True


def _is_caption_row(grid: Grid, row: int) -> bool:
    if grid.num_cols < 2:
        return False  # Can't have caption rows in single-column tables
    cell = grid.get(row, 0)
    if not cell:
        return False
    texts = [grid.text(row, c).strip() for c in range(grid.num_cols)]
    non_empty = [t for t in texts if t]
    return cell.col_span >= grid.num_cols - 1 and len(non_empty) == 1 and bool(cell.text.strip())


def _is_schema_break(grid: Grid, sub_start: int, row: int) -> bool:
    """Check if row starts a new schema compared to the sub-table's first data row."""
    sub_header_types = [classify_cell_type(grid.text(sub_start, c)) for c in range(grid.num_cols)]
    row_types = [classify_cell_type(grid.text(row, c)) for c in range(grid.num_cols)]

    # If the row looks like all headers again after data rows
    non_empty_header = [t for t in sub_header_types if t != DataType.EMPTY]
    non_empty_row = [t for t in row_types if t != DataType.EMPTY]

    if len(non_empty_row) == 0:
        return True

    # If all cells are categorical after having numeric data, it's a new header
    if all(t == DataType.CATEGORICAL for t in non_empty_row) and len(non_empty_row) >= 2:
        return True

    return False


def _count_non_empty_cols(grid: Grid, start: int, end: int) -> int:
    count = 0
    for c in range(grid.num_cols):
        for r in range(start, end):
            if grid.text(r, c).strip():
                count += 1
                break
    return count


def _analyze_compound(raw: RawTable, grid: Grid, boundaries: list[tuple[int, int]]) -> SemanticTable:
    """Analyze a compound table by analyzing each sub-table region."""
    sub_tables: list[SubTable] = []

    # Shared headers captured from the first sub-table and reused for subsequent ones
    shared_columns: list[ColumnDef] | None = None
    shared_column_headers: list[HeaderCell] | None = None
    shared_header_row_count: int = 0
    shared_header_col_count: int = 0

    for idx, (start, end) in enumerate(boundaries):
        caption = None
        data_start = start

        if _is_caption_row(grid, start):
            first_cell = grid.get(start, 0)
            caption = first_cell.text.strip() if first_cell else None
            data_start = start + 1
        elif _is_category_separator_row(grid, start):
            caption = grid.text(start, 0).strip()
            data_start = start + 1

        if data_start >= end:
            continue

        sub_grid_full = _extract_sub_grid(grid, data_start, end, 0, grid.num_cols)
        sbs_groups = _find_side_by_side_groups(sub_grid_full)
        use_shared = shared_columns is not None and _first_row_is_data(sub_grid_full)

        if len(sbs_groups) >= 2:
            for g_idx, (col_start, col_end) in enumerate(sbs_groups):
                sub_grid = _extract_sub_grid(grid, data_start, end, col_start, col_end)
                if use_shared:
                    sub_header_row_count = 0
                    sub_header_col_count = shared_header_col_count
                    sub_columns = [c for c in shared_columns if col_start <= c.index < col_end]
                    sub_col_headers = [
                        h for h in (shared_column_headers or [])
                        if h.col_range is None or (
                            h.col_range[0] >= col_start and h.col_range[1] <= col_end
                        )
                    ]
                else:
                    sub_header_row_count = _detect_header_row_count(sub_grid)
                    sub_header_col_count = _detect_header_col_count(sub_grid)
                    sub_columns = _extract_columns(sub_grid, sub_header_row_count)
                    sub_col_headers = _build_column_headers(sub_grid, sub_header_row_count)

                sub_row_headers = _build_row_headers(sub_grid, sub_header_row_count, sub_header_col_count)
                sub_rows = _extract_rows(sub_grid, sub_header_row_count, sub_header_col_count, TablePattern.ROW)
                sub_table_type, _, _ = _classify_table_type(
                    sub_grid, sub_columns, sub_header_row_count, sub_header_col_count, TablePattern.ROW
                )
                sub_agg_rows = _detect_aggregate_rows(sub_grid, sub_header_row_count, sub_header_col_count)

                if not use_shared:
                    shared_columns = [c for c in sub_columns]
                    shared_column_headers = sub_col_headers
                    shared_header_row_count = sub_header_row_count
                    shared_header_col_count = sub_header_col_count

                sub_rows = _merge_continuation_rows(sub_rows, sub_grid, sub_header_row_count)

                sub_tables.append(
                    SubTable(
                        index=len(sub_tables),
                        caption=f"{caption} (Group {g_idx + 1})" if caption else None,
                        column_headers=sub_col_headers,
                        row_headers=sub_row_headers,
                        columns=sub_columns,
                        rows=sub_rows,
                        data_bounds=(data_start, col_start, end, col_end),
                        table_type=sub_table_type,
                        aggregate_rows=sub_agg_rows,
                    )
                )
        else:
            sub_grid = _extract_sub_grid(grid, data_start, end, 0, grid.num_cols)
            if use_shared:
                sub_header_row_count = 0
                sub_header_col_count = shared_header_col_count
                sub_columns = list(shared_columns)
                sub_col_headers = list(shared_column_headers) if shared_column_headers else []
            else:
                sub_header_row_count = _detect_header_row_count(sub_grid)
                sub_header_col_count = _detect_header_col_count(sub_grid)
                sub_columns = _extract_columns(sub_grid, sub_header_row_count)
                sub_col_headers = _build_column_headers(sub_grid, sub_header_row_count)

            sub_row_headers = _build_row_headers(sub_grid, sub_header_row_count, sub_header_col_count)
            sub_rows = _extract_rows(sub_grid, sub_header_row_count, sub_header_col_count, TablePattern.ROW)
            sub_table_type, _, _ = _classify_table_type(
                sub_grid, sub_columns, sub_header_row_count, sub_header_col_count, TablePattern.ROW
            )
            sub_agg_rows = _detect_aggregate_rows(sub_grid, sub_header_row_count, sub_header_col_count)

            if not use_shared:
                shared_columns = [c for c in sub_columns]
                shared_column_headers = sub_col_headers
                shared_header_row_count = sub_header_row_count
                shared_header_col_count = sub_header_col_count

            sub_rows = _merge_continuation_rows(sub_rows, sub_grid, sub_header_row_count)

            sub_tables.append(
                SubTable(
                    index=idx,
                    caption=caption,
                    column_headers=sub_col_headers,
                    row_headers=sub_row_headers,
                    columns=sub_columns,
                    rows=sub_rows,
                    data_bounds=(start, 0, end, grid.num_cols),
                    table_type=sub_table_type,
                    aggregate_rows=sub_agg_rows,
                )
            )

    return SemanticTable(
        raw=raw,
        table_pattern=TablePattern.STACKED,
        is_compound=True,
        sub_tables=sub_tables,
        parse_confidence=1.0,
    )


def _first_row_is_data(grid: Grid) -> bool:
    """Check if the first row of a sub-grid contains numeric data (not headers)."""
    if grid.num_rows == 0:
        return False
    for c in range(grid.num_cols):
        if is_numeric(grid.text(0, c)):
            return True
    return False


def _extract_sub_grid(grid: Grid, start_row: int, end_row: int, start_col: int = 0, end_col: int | None = None) -> Grid:
    """Create a Grid for a sub-region [start_row, end_row) x [start_col, end_col)."""
    from table_analyzer.models import RawCell

    if end_col is None:
        end_col = grid.num_cols

    num_rows = end_row - start_row
    num_cols = end_col - start_col

    cells = []
    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            cell = grid.get(r, c)
            if cell:
                new_row_span = min(cell.row_span, end_row - r)
                new_col_span = min(cell.col_span, end_col - c)
                cells.append(
                    RawCell(
                        row=r - start_row,
                        col=c - start_col,
                        text=cell.text,
                        row_span=new_row_span,
                        col_span=new_col_span,
                    )
                )

    grid_rows = [[None] * num_cols for _ in range(num_rows)]
    for cell in cells:
        if 0 <= cell.row < num_rows and 0 <= cell.col < num_cols:
            grid_rows[cell.row][cell.col] = cell

    return Grid(cells=grid_rows, num_rows=num_rows, num_cols=num_cols)


# ── Pattern Detection ──────────────────────────────────────────────────────


def _detect_pattern(grid: Grid) -> TablePattern:
    # Check sparse/diagonal first
    if _is_sparse(grid):
        return TablePattern.SPARSE

    # Check hierarchical
    if _is_hierarchical(grid):
        return TablePattern.HIERARCHICAL

    # Check multi-header
    if _is_multi_header(grid):
        return TablePattern.MULTI_HEADER

    # Check side-by-side
    if _is_side_by_side(grid):
        return TablePattern.SIDE_BY_SIDE

    # Check form
    if _is_form(grid):
        return TablePattern.FORM

    # Check transposed
    if _is_transposed(grid):
        return TablePattern.TRANSPOSED

    # Default: row table
    return TablePattern.ROW


def _is_side_by_side(grid: Grid) -> bool:
    """Detect if the table has repeated column header sequences side by side.

    e.g., cols 0-3 have 车系|品牌|车型|价格 and cols 4-7 repeat the same.
    """
    if grid.num_cols < 4:
        return False

    # Get the first row of headers
    header_row = 0
    # Skip category separator rows
    if _is_category_separator_row(grid, 0):
        header_row = 1

    if header_row >= grid.num_rows:
        return False

    # Get the header texts
    headers = [grid.text(header_row, c).strip() for c in range(grid.num_cols)]

    # Try different group sizes
    for group_size in range(2, grid.num_cols // 2 + 1):
        if grid.num_cols % group_size != 0:
            continue
        num_groups = grid.num_cols // group_size
        if num_groups < 2:
            continue

        first_group = headers[:group_size]
        if not all(first_group):
            continue

        # Check if all groups match the first
        all_match = True
        for g in range(1, num_groups):
            group = headers[g * group_size : (g + 1) * group_size]
            if group != first_group:
                all_match = False
                break

        if all_match:
            return True

    return False


def _find_side_by_side_groups(grid: Grid) -> list[tuple[int, int]]:
    """Find the column boundaries of side-by-side groups.

    Returns list of (start_col, end_col) tuples.
    """
    if grid.num_cols < 4:
        return [(0, grid.num_cols)]

    header_row = 0
    if _is_category_separator_row(grid, 0):
        header_row = 1

    if header_row >= grid.num_rows:
        return [(0, grid.num_cols)]

    headers = [grid.text(header_row, c).strip() for c in range(grid.num_cols)]

    for group_size in range(2, grid.num_cols // 2 + 1):
        if grid.num_cols % group_size != 0:
            continue
        num_groups = grid.num_cols // group_size
        if num_groups < 2:
            continue

        first_group = headers[:group_size]
        if not all(first_group):
            continue

        all_match = True
        for g in range(1, num_groups):
            group = headers[g * group_size : (g + 1) * group_size]
            if group != first_group:
                all_match = False
                break

        if all_match:
            return [(g * group_size, (g + 1) * group_size) for g in range(num_groups)]

    return [(0, grid.num_cols)]


def _is_sparse(grid: Grid) -> bool:
    if grid.num_rows != grid.num_cols:
        return False
    if grid.num_rows < 3:
        return False
    # Check that row headers match column headers
    for i in range(1, grid.num_rows):
        row_header = grid.text(i, 0).strip()
        col_header = grid.text(0, i).strip()
        if row_header != col_header:
            return False
    return True


def _is_hierarchical(grid: Grid) -> bool:
    if grid.num_rows < 4:
        return False
    # Check for indented rows (leading whitespace)
    indented = 0
    for r in range(1, grid.num_rows):
        text = grid.text(r, 0)
        if text and text[0] in (" ", "\t"):
            indented += 1
    if indented >= 2:
        return True

    # Also check for bold formatting alternation (parent bold, child not)
    bold_count = 0
    non_bold_count = 0
    for r in range(1, grid.num_rows):
        cell = grid.get(r, 0)
        if cell and cell.text.strip():
            if cell.is_bold:
                bold_count += 1
            elif cell.is_bold is False:
                non_bold_count += 1
    if bold_count >= 2 and non_bold_count >= 2:
        return True

    # Check for empty cells in row-header column ("same as above" pattern)
    # E.g.: 杭州, <empty>, <empty>, 上海, <empty> → hierarchical grouping
    empty_header_cells = 0
    for r in range(1, grid.num_rows):
        col0 = grid.text(r, 0).strip()
        if not col0 and grid.text(r, 1).strip():
            empty_header_cells += 1
    if empty_header_cells >= 2:
        return True

    return False


def _is_multi_header(grid: Grid) -> bool:
    if grid.num_rows < 3:
        return False
    # Check if row 0 has merged cells (col_span > 1)
    has_merge = False
    for c in range(grid.num_cols):
        cell = grid.get(0, c)
        if cell and cell.col_span > 1:
            has_merge = True
            break
    if not has_merge:
        return False
    # Row 1 should look like headers (mostly categorical)
    row1_types = [classify_cell_type(grid.text(1, c)) for c in range(grid.num_cols)]
    non_empty = [t for t in row1_types if t != DataType.EMPTY]
    return len(non_empty) > 0 and all(t == DataType.CATEGORICAL for t in non_empty)


def _is_form(grid: Grid) -> bool:
    if grid.num_cols != 2:
        return False
    if grid.num_rows < 3:
        return False
    # First column: all unique categorical values in data rows
    values = set()
    for r in range(1, grid.num_rows):
        text = grid.text(r, 0).strip()
        if not text:
            return False
        if classify_cell_type(text) != DataType.CATEGORICAL:
            return False
        values.add(text)
    return len(values) == grid.num_rows - 1


def _is_transposed(grid: Grid) -> bool:
    """Transposed: metrics as row headers, time periods as column headers.

    Distinguished from a normal row table by: ALL non-empty column headers
    (cols 1+) are temporal, col 0 header is a non-empty categorical label
    (like "Metric"), and row headers (rows 1+) are metric-like names
    (not entity values like region names).
    """
    if grid.num_rows < 3 or grid.num_cols < 3:
        return False

    # Col 0 header must be a non-empty categorical label (e.g., "Metric")
    col0_header = grid.text(0, 0).strip()
    if not col0_header or classify_cell_type(col0_header) != DataType.CATEGORICAL:
        return False

    # All non-empty column headers (cols 1+) should be temporal
    non_empty_col_headers = 0
    temporal_col_headers = 0
    for c in range(1, grid.num_cols):
        text = grid.text(0, c).strip()
        if not text:
            continue
        non_empty_col_headers += 1
        if classify_cell_type(text) == DataType.TEMPORAL:
            temporal_col_headers += 1

    if non_empty_col_headers == 0 or temporal_col_headers < non_empty_col_headers:
        return False

    # Row headers should be categorical with numeric data
    categorical_rows = 0
    for r in range(1, grid.num_rows):
        row_header = grid.text(r, 0).strip()
        if not row_header or classify_cell_type(row_header) != DataType.CATEGORICAL:
            continue
        numeric_count = sum(1 for c in range(1, grid.num_cols) if is_numeric(grid.text(r, c)))
        if numeric_count >= 2:
            categorical_rows += 1

    return categorical_rows >= 2


# ── Header Detection ───────────────────────────────────────────────────────


def _detect_headers(grid: Grid, pattern: TablePattern) -> tuple[int, int]:
    if pattern == TablePattern.FORM:
        # Form tables always have exactly 1 header row
        return 1, 0
    header_rows = _detect_header_row_count(grid)
    header_cols = _detect_header_col_count(grid)
    return header_rows, header_cols


def _detect_header_row_count(grid: Grid) -> int:
    if grid.num_rows < 2:
        return min(1, grid.num_rows)

    # If formatting hints are available, use them
    has_hints = any(
        grid.get(r, c) and grid.get(r, c).is_header is not None
        for r in range(min(3, grid.num_rows))
        for c in range(grid.num_cols)
    )
    if has_hints:
        header_rows = 0
        for r in range(grid.num_rows):
            row_is_header = False
            for c in range(grid.num_cols):
                cell = grid.get(r, c)
                if cell and cell.is_header:
                    row_is_header = True
                    break
            if row_is_header:
                header_rows = r + 1
            else:
                break
        if header_rows > 0:
            return header_rows

    # Fallback: type-based detection
    for r in range(grid.num_rows):
        row_types = [classify_cell_type(grid.text(r, c)) for c in range(grid.num_cols)]
        non_empty = [t for t in row_types if t != DataType.EMPTY]
        if not non_empty:
            continue
        if any(t == DataType.NUMERIC for t in non_empty):
            return max(1, r)
    return 1


def _detect_header_col_count(grid: Grid) -> int:
    if grid.num_cols < 2:
        return 0
    header_row_count = _detect_header_row_count(grid)
    count = 0
    for c in range(grid.num_cols):
        is_categorical = True
        for r in range(header_row_count, grid.num_rows):
            text = grid.text(r, c)
            if is_numeric(text):
                is_categorical = False
                break
        if is_categorical:
            count += 1
        else:
            break
    return min(count, 2)  # Support up to 2 row header columns (e.g., category + subcategory)


# ── Schema Extraction ──────────────────────────────────────────────────────


def _extract_columns(grid: Grid, header_row_count: int) -> list[ColumnDef]:
    columns = []
    header_row = max(0, header_row_count - 1)  # Use last header row for column names
    for c in range(grid.num_cols):
        name = grid.text(header_row, c).strip()
        if not name:
            continue
        # Determine data type from data rows
        types: list[DataType] = []
        for r in range(header_row_count, grid.num_rows):
            text = grid.text(r, c)
            t = classify_cell_type(text)
            if t != DataType.EMPTY:
                types.append(t)

        data_type = _majority_type(types) if types else DataType.CATEGORICAL

        # Extract unit from column name
        unit = _extract_unit_from_header(name)

        columns.append(ColumnDef(index=c, name=name, data_type=data_type, unit=unit))

    # Disambiguate duplicate column names using super-header row
    if header_row_count >= 2:
        name_counts: dict[str, int] = {}
        for col in columns:
            name_counts[col.name] = name_counts.get(col.name, 0) + 1
        duplicates = {n for n, c in name_counts.items() if c > 1}
        if duplicates:
            for col in columns:
                if col.name in duplicates:
                    super_header = grid.text(0, col.index).strip()
                    if super_header:
                        col.name = f"{super_header}-{col.name}"

    return columns


def _extract_rows(
    grid: Grid, header_row_count: int, header_col_count: int, pattern: TablePattern
) -> list[RowDef]:
    rows = []
    if header_col_count == 0:
        for r in range(header_row_count, grid.num_rows):
            rows.append(RowDef(index=r))
        return rows

    if pattern == TablePattern.HIERARCHICAL:
        return _extract_hierarchical_rows(grid, header_row_count, header_col_count)

    for r in range(header_row_count, grid.num_rows):
        header_val = grid.text(r, 0).strip()
        data_type = classify_cell_type(header_val)
        rows.append(RowDef(index=r, header_value=header_val, data_type=data_type))
    return rows


def _extract_hierarchical_rows(grid: Grid, header_row_count: int, header_col_count: int) -> list[RowDef]:
    rows = []
    current_parent: str | None = None

    for r in range(header_row_count, grid.num_rows):
        text = grid.text(r, 0)
        header_val = text.strip()
        level = 0
        parent = None

        if not header_val:
            # Empty cell → "same as above": child of current parent group
            level = 1
            parent = current_parent
            header_val = current_parent or ""
        elif text and text[0] in (" ", "\t"):
            level = 1
            parent = current_parent
        else:
            current_parent = header_val

        rows.append(RowDef(index=r, header_value=header_val, level=level, parent=parent))
    return rows


_CONTINUATION_MARKERS = frozenset({"%", "％", "占比", "yoy", "y/y", "qoq", "q/q"})


def _merge_continuation_rows(rows: list[RowDef], grid: Grid, header_row_count: int) -> list[RowDef]:
    """Merge continuation rows (e.g. % sub-rows) into their parent rows."""
    if len(rows) < 2:
        return rows

    result: list[RowDef] = []
    i = 0
    while i < len(rows):
        row = rows[i]
        header = (row.header_value or "").strip().lower()

        # Check if this looks like a continuation of the previous row
        if result and header in _CONTINUATION_MARKERS:
            parent = result[-1]
            parent.sub_rows.append(row)
            row.continuation_of = parent.index
            i += 1
            continue

        # Also check: row with "%" in col 0 or empty header following a labeled row
        # e.g., "原材料及消耗品费用" followed by "%" row
        if result and (not header or header in _CONTINUATION_MARKERS):
            prev = result[-1]
            prev_header = (prev.header_value or "").strip()
            if prev_header and prev_header not in _CONTINUATION_MARKERS:
                prev.sub_rows.append(row)
                row.continuation_of = prev.index
                i += 1
                continue

        result.append(row)
        i += 1

    return result


def _majority_type(types: list[DataType]) -> DataType:
    if not types:
        return DataType.CATEGORICAL
    counts: dict[DataType, int] = {}
    for t in types:
        counts[t] = counts.get(t, 0) + 1
    return max(counts, key=lambda k: counts[k])


# ── Aggregate Detection ────────────────────────────────────────────────────

_AGGREGATE_KEYWORDS = {
    "total", "subtotal", "grand total", "sum", "average", "mean", "all", "overall",
    "合计", "总计", "小计", "全部", "累计",
}

# Marker characters that may follow an aggregate keyword (e.g., "合计：", "合计:")
_AGGREGATE_MARKER_SUFFIX = frozenset({"：", ":", "(", "（", " ", "\t"})


def _is_aggregate_header(text: str) -> bool:
    """Check if a row header text indicates an aggregate row (not a metric name)."""
    t = text.strip().lower()
    if not t:
        return False
    for kw in _AGGREGATE_KEYWORDS:
        if t == kw:
            return True
        if t.startswith(kw) and len(t) > len(kw) and t[len(kw)] in _AGGREGATE_MARKER_SUFFIX:
            return True
    return False


def _detect_aggregate_rows(grid: Grid, header_row_count: int, header_col_count: int) -> list[AggregateDef]:
    aggregates = []
    for r in range(header_row_count, grid.num_rows):
        header_text = grid.text(r, header_col_count).strip() if header_col_count < grid.num_cols else ""
        first_text = grid.text(r, 0).strip()

        is_agg_keyword = _is_aggregate_header(first_text) or _is_aggregate_header(header_text)

        if not is_agg_keyword:
            continue

        agg_type = AggregateType.SUM
        if "average" in first_text or "mean" in first_text:
            agg_type = AggregateType.AVERAGE
        elif "percentage" in first_text or "%" in first_text:
            agg_type = AggregateType.PERCENTAGE

        # Verify mathematically if possible
        if agg_type == AggregateType.SUM and _verify_sum(grid, r, header_row_count, header_col_count):
            aggregates.append(AggregateDef(index=r, aggregate_type=agg_type))
        elif is_agg_keyword:
            aggregates.append(AggregateDef(index=r, aggregate_type=agg_type))

    return aggregates


def _verify_sum(grid: Grid, agg_row: int, header_row_count: int, header_col_count: int) -> bool:
    """Check if the aggregate row equals the sum of non-aggregate rows above it."""
    # Find the nearest preceding aggregate or header
    start = header_row_count
    for r in range(agg_row - 1, header_row_count - 1, -1):
        first_text = grid.text(r, 0).strip()
        if _is_aggregate_header(first_text):
            start = r + 1
            break

    verified = False
    for c in range(header_col_count, grid.num_cols):
        total = 0.0
        valid = True
        for r in range(start, agg_row):
            val = parse_numeric(grid.text(r, c))
            if val is None:
                valid = False
                break
            total += val

        if not valid:
            continue

        agg_val = parse_numeric(grid.text(agg_row, c))
        if agg_val is not None and abs(total - agg_val) < 0.01 * max(abs(total), 1):
            verified = True
            break

    return verified


# ── Table Type Classification ──────────────────────────────────────────────


def _classify_table_type(
    grid: Grid, columns: list[ColumnDef], header_row_count: int, header_col_count: int, pattern: TablePattern
) -> tuple[TableType, str | None, list[TimePoint]]:
    if pattern == TablePattern.FORM:
        return TableType.PARAMETER_SPEC, None, []

    # Check for temporal dimension
    temporal_col, temporal_values = _find_temporal_columns(grid, columns, header_row_count, header_col_count)
    if temporal_col is not None:
        return TableType.TIME_SERIES, "columns", temporal_values

    temporal_row, temporal_values_rows = _find_temporal_rows(grid, header_row_count, header_col_count)
    if temporal_row is not None:
        return TableType.TIME_SERIES, "rows", temporal_values_rows

    if pattern == TablePattern.HIERARCHICAL:
        return TableType.HIERARCHICAL_SUMMARY, None, []

    if pattern == TablePattern.SPARSE:
        return TableType.CROSS_TAB, None, []

    return TableType.COMPARISON, None, []


def _find_temporal_columns(
    grid: Grid, columns: list[ColumnDef], header_row_count: int, header_col_count: int = 0
) -> tuple[int | None, list[TimePoint]]:
    temporal_cols = []
    for col in columns:
        if col.data_type == DataType.TEMPORAL:
            temporal_cols.append(col.index)
        if _is_temporal_text(col.name):
            temporal_cols.append(col.index)

    # Check data rows for temporal content (skip row header columns)
    for c in range(header_col_count, grid.num_cols):
        temporal_count = 0
        for r in range(header_row_count, grid.num_rows):
            if classify_cell_type(grid.text(r, c)) == DataType.TEMPORAL:
                temporal_count += 1
        if temporal_count >= 2:
            temporal_cols.append(c)

    if not temporal_cols:
        return None, []

    # Parse temporal values from the first temporal column's header
    values = []
    for c in set(temporal_cols):
        for r in range(header_row_count):
            text = grid.text(r, c)
            if _is_temporal_text(text):
                values.append(_parse_temporal(text))
    return temporal_cols[0], values


def _find_temporal_rows(grid: Grid, header_row_count: int, header_col_count: int) -> tuple[int | None, list[TimePoint]]:
    # Check data columns first (starting from header_col_count)
    for start_col in range(header_col_count, grid.num_cols):
        values = []
        for r in range(header_row_count, grid.num_rows):
            text = grid.text(r, start_col)
            if _is_temporal_text(text):
                values.append(_parse_temporal(text))
        if values:
            return start_col, values

    # Also check row header column (col 0) — temporal values can be row headers
    if header_col_count > 0:
        values = []
        for r in range(header_row_count, grid.num_rows):
            text = grid.text(r, 0)
            if _is_temporal_text(text):
                values.append(_parse_temporal(text))
        if values:
            return 0, values

    return None, []


def _is_temporal_text(text: str) -> bool:
    if not text:
        return False
    return classify_cell_type(text) == DataType.TEMPORAL or bool(
        re.match(r"Q[1-4]\s*\d{4}", text, re.IGNORECASE)
    )


def _parse_temporal(text: str) -> TimePoint:
    t = text.strip()
    tp = TimePoint(raw=t)

    # Chinese: 2022年1-5月 (year + month range)
    m = re.match(r"(\d{4})年(\d{1,2})-(\d{1,2})月?$", t)
    if m:
        tp.year = int(m.group(1))
        tp.month = int(m.group(2))
        tp.period = "month_range"
        return tp

    # Chinese: 2022年1月 (year + month)
    m = re.match(r"(\d{4})年(\d{1,2})月?$", t)
    if m:
        tp.year = int(m.group(1))
        tp.month = int(m.group(2))
        tp.period = "month"
        return tp

    # Chinese: 2021年 (year only)
    m = re.match(r"(\d{4})年$", t)
    if m:
        tp.year = int(m.group(1))
        tp.period = "year"
        return tp

    # Q1 2024, Q2 2024, etc.
    m = re.match(r"Q(\d)\s*(\d{4})", t, re.IGNORECASE)
    if m:
        tp.quarter = int(m.group(1))
        tp.year = int(m.group(2))
        tp.period = "quarter"
        return tp

    # YYYY-MM-DD
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        tp.year = int(m.group(1))
        tp.month = int(m.group(2))
        tp.date = t
        tp.period = "date"
        return tp

    # Bare year: "2021", "2022"
    m = re.match(r"^(19\d{2}|20\d{2})$", t)
    if m:
        tp.year = int(m.group(1))
        tp.period = "year"
        return tp

    # Year+quarter: "2023Q1"
    m = re.match(r"^(19\d{2}|20\d{2})Q(\d)$", t, re.IGNORECASE)
    if m:
        tp.year = int(m.group(1))
        tp.quarter = int(m.group(2))
        tp.period = "quarter"
        return tp

    # Month name
    months = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
        "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "september": 9,
        "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
    }
    lower = t.lower()
    for name, num in months.items():
        if lower.startswith(name):
            tp.month = num
            tp.period = "month"
            return tp

    return tp


# ── Unit Resolution ────────────────────────────────────────────────────────


def _resolve_units(raw: RawTable, grid: Grid, header_row_count: int) -> tuple[str | None, dict[int, str], UnitSource | None]:
    default_unit = None
    unit_source = None
    column_units: dict[int, str] = {}

    # From caption: "Table X: ... (Unit)"
    if raw.caption:
        m = re.search(r"\(([^)]+)\)\s*$", raw.caption)
        if m:
            default_unit = m.group(1).strip()
            unit_source = UnitSource.CAPTION

    # From column headers: "Revenue ($M)"
    for c in range(grid.num_cols):
        for r in range(header_row_count):
            text = grid.text(r, c)
            m = re.search(r"\(([^)]+)\)", text)
            if m:
                unit = m.group(1).strip()
                column_units[c] = unit
                if unit_source is None:
                    unit_source = UnitSource.COLUMN_HEADER

    # From footnotes: "All values in ..."
    for fn in raw.footnotes:
        m = re.search(r"(?:all values|values) (?:are )?in (.+?)(?:\.|$)", fn, re.IGNORECASE)
        if m:
            default_unit = m.group(1).strip()
            unit_source = UnitSource.FOOTNOTE

    return default_unit, column_units, unit_source


# ── Annotation Extraction ──────────────────────────────────────────────────


def _extract_annotations(grid: Grid, footnotes: list[str], header_row_count: int) -> list[Annotation]:
    if not footnotes:
        return []

    annotations = []

    # Build symbol -> footnote mapping
    symbol_map: dict[str, str] = {}
    for fn in footnotes:
        m = re.match(r"^([*†‡§¶]+)\s+(.+)$", fn.strip())
        if m:
            symbol_map[m.group(1)] = m.group(2).strip()

    if not symbol_map:
        return []

    # Scan data cells for trailing symbols
    for r in range(header_row_count, grid.num_rows):
        for c in range(grid.num_cols):
            text = grid.text(r, c).strip()
            # Match trailing annotation symbols
            m = re.search(r"([*†‡§¶]+)$", text)
            if m:
                symbol = m.group(1)
                if symbol in symbol_map:
                    annotations.append(
                        Annotation(
                            symbol=symbol,
                            row=r,
                            col=c,
                            cell_text=text,
                            footnote_text=symbol_map[symbol],
                        )
                    )

    return annotations


# ── Fingerprint ────────────────────────────────────────────────────────────


def _compute_fingerprint(columns: list[ColumnDef], header_row_count: int, header_col_count: int) -> str:
    parts = [
        tuple(col.name.lower().strip() for col in columns),
        tuple(col.data_type.value for col in columns),
        header_row_count,
        header_col_count,
    ]
    return hashlib.md5(str(parts).encode()).hexdigest()


# ── Instance Context ───────────────────────────────────────────────────────

# Common dimension keywords found in captions
_DIMENSION_PATTERNS = [
    (r"(APAC|EMEA|Americas?|Europe|Asia|Africa)\s+", "Region"),
    (r"(Q[1-4]\s*\d{4})\s+", "Quarter"),
    (r"(FY\s*\d{2,4})\s+", "Fiscal Year"),
    (r"(\d{4})\s+", "Year"),
]


def _extract_instance_context(raw: RawTable) -> InstanceContext | None:
    if not raw.caption:
        return None

    caption = raw.caption.strip()

    # First: try known entity prefixes for the implicit dimension
    # "APAC Revenue by Quarter" → "APAC" is a region, so implicit dimension = "Region"
    for pattern, dimension in _DIMENSION_PATTERNS:
        m = re.match(pattern, caption, re.IGNORECASE)
        if m:
            return InstanceContext(
                dimension=dimension,
                value=m.group(1).strip(),
                source="caption",
                confidence=0.9,
            )

    # Second: "X Metric by Dimension" pattern → X is the instance value
    # Only use this if no entity prefix matched, since the "by" gives the
    # table's explicit dimension, not the implicit one
    m = re.match(r"^(.+?)\s+\w+\s+by\s+(\w+)", caption, re.IGNORECASE)
    if m:
        value = m.group(1).strip()
        value = re.sub(r"^Table\s+\d+:\s*", "", value, flags=re.IGNORECASE).strip()
        if value:
            return InstanceContext(dimension="Entity", value=value, source="caption", confidence=0.7)

    return None


# ── Header Builders ────────────────────────────────────────────────────────


def _build_column_headers(grid: Grid, header_row_count: int) -> list[HeaderCell]:
    headers = []
    for r in range(header_row_count):
        for c in range(grid.num_cols):
            text = grid.text(r, c)
            if not text:
                continue
            cell = grid.get(r, c)
            col_span = cell.col_span if cell else 1
            headers.append(
                HeaderCell(
                    text=text,
                    level=r,
                    col_span=col_span,
                    col_range=(c, c + col_span) if col_span > 1 else None,
                )
            )
    return headers


def _build_row_headers(grid: Grid, header_row_count: int, header_col_count: int) -> list[HeaderCell]:
    if header_col_count == 0:
        return []
    headers = []
    for r in range(header_row_count, grid.num_rows):
        text = grid.text(r, 0)
        if text:
            headers.append(HeaderCell(text=text))
    return headers


# ── Unit Helper ────────────────────────────────────────────────────────────


def _extract_unit_from_header(name: str) -> str | None:
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        return m.group(1).strip()
    return None

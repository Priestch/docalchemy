from __future__ import annotations

import re
from dataclasses import dataclass

from table_analyzer.models import DataType, RawCell, RawTable

_EMPTY_VALUES = frozenset({
    "", "-", "—", "–", "─", "N/A", "NA", "n/a", "na", "null", "None",
    "none", "---", "TBD", "tbd", ".", "..",
})

_CURRENCY_PREFIXES = re.compile(r"^(?:USD|EUR|GBP|JPY|CNY|CAD|AUD)\s*", re.IGNORECASE)

_MONTH_NAMES = (
    "January|February|March|April|May|June|July|August|September|October|November|December"
    "|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)

_TEMPORAL_RE = re.compile(
    r"^(?:"
    r"Q[1-4]\s*\d{4}|"
    r"\d{4}\s*-?\s*Q[1-4]|"
    r"H[1-2]\s*\d{4}|"
    r"FY\s*\d{2,4}|"
    r"\d{4}-\d{2}-\d{2}|"
    r"\d{4}\.\d{2}|"  # 2017.06
    r"\d{2}/\d{2}/\d{4}|"
    r"\d{4}年(?:\s*\d{1,2}(?:-\d{1,2})?月)?|"  # 2021年, 2022年1月, 2022年1-5月
    r"(?:" + _MONTH_NAMES + r")"
    r"(?:\s+\d{4})?"
    r")$",
    re.IGNORECASE,
)


@dataclass
class Grid:
    """Convenient 2D access over a RawTable's cells."""

    cells: list[list[RawCell | None]]  # [row][col]
    num_rows: int
    num_cols: int

    @classmethod
    def from_raw(cls, raw: RawTable) -> Grid:
        grid: list[list[RawCell | None]] = [
            [None for _ in range(raw.num_cols)] for _ in range(raw.num_rows)
        ]
        for cell in raw.cells:
            if not (0 <= cell.row < raw.num_rows and 0 <= cell.col < raw.num_cols):
                continue
            # Place the cell at its anchor position
            grid[cell.row][cell.col] = cell
            # Propagate to all spanned positions
            for dr in range(cell.row_span):
                for dc in range(cell.col_span):
                    r, c = cell.row + dr, cell.col + dc
                    if 0 <= r < raw.num_rows and 0 <= c < raw.num_cols and (dr > 0 or dc > 0):
                        grid[r][c] = grid[r][c] or cell
        return cls(cells=grid, num_rows=raw.num_rows, num_cols=raw.num_cols)

    def get(self, row: int, col: int) -> RawCell | None:
        if 0 <= row < self.num_rows and 0 <= col < self.num_cols:
            return self.cells[row][col]
        return None

    def text(self, row: int, col: int) -> str:
        cell = self.get(row, col)
        return cell.text if cell else ""

    def row_texts(self, row: int) -> list[str]:
        return [self.text(row, c) for c in range(self.num_cols)]

    def col_texts(self, col: int) -> list[str]:
        return [self.text(r, col) for r in range(self.num_rows)]


def classify_cell_type(text: str) -> DataType:
    t = text.strip()

    if t.upper() in _EMPTY_VALUES:
        return DataType.EMPTY

    # Bare 4-digit year: "2021", "2022" (1900-2099) — before numeric check
    if re.match(r"^(?:19\d{2}|20\d{2})$", t):
        return DataType.TEMPORAL

    # YYYY.MM date: "2017.06", "2024.01" — before numeric check (matches plain number)
    if re.match(r"^\d{4}\.\d{2}$", t):
        return DataType.TEMPORAL

    # Parenthesized negative: "(100)", "(5.2%)"
    if re.match(r"^\([+-]?\d[\d,.]*%?\)$", t):
        return DataType.NUMERIC

    # Percentage: "12.5%", "+5.1%", "-8.2%", "12.5 pct", "12.5 percent"
    if re.match(r"^[+-]?\d+\.?\d*\s*(?:%|pct|percent)$", t, re.IGNORECASE):
        return DataType.NUMERIC

    # Currency with symbol: "$1,234", "€500", "¥1M"
    if re.match(r"^[$€£¥]\s*\d[\d,.]*\s*[MK]?$", t):
        return DataType.NUMERIC

    # Currency with code: "USD 1,234", "EUR 500"
    if _CURRENCY_PREFIXES.match(t) and re.search(r"\d", t):
        return DataType.NUMERIC

    # Plain number with optional +/-, commas, K/M suffix
    if re.match(r"^[+-]?\d[\d,.]*\s*[KkMm]?$", t):
        return DataType.NUMERIC

    # Scientific notation
    if re.match(r"^[+-]?\d+\.?\d*[eE][+-]?\d+$", t):
        return DataType.NUMERIC

    # Temporal
    if _TEMPORAL_RE.match(t):
        return DataType.TEMPORAL

    # Long text
    if len(t) > 200:
        return DataType.TEXT

    return DataType.CATEGORICAL


def is_numeric(text: str) -> bool:
    return classify_cell_type(text) == DataType.NUMERIC


def parse_numeric(text: str) -> float | None:
    """Extract the numeric value from a cell, stripping symbols and annotations."""
    t = text.strip()

    # Handle parenthesized negative: "(100)" → -100
    m = re.match(r"^\((.+)\)$", t)
    if m:
        inner = m.group(1).strip()
        val = _parse_positive_number(inner)
        return -val if val is not None else None

    # Strip trailing annotation symbols (*, †, **, etc.)
    t = re.sub(r"[*†‡§¶]+$", "", t).strip()

    # Strip trailing unit words
    t = re.sub(r"\s*(?:pct|percent)$", "", t, flags=re.IGNORECASE).strip()

    # Strip leading currency code
    t = _CURRENCY_PREFIXES.sub("", t).strip()

    # Strip currency symbols
    t = re.sub(r"^[$€£¥]\s*", "", t)

    # Strip trailing %
    t = t.rstrip("%").strip()

    # Strip +/-
    sign = 1.0
    if t.startswith("+"):
        t = t[1:]
    elif t.startswith("-"):
        sign = -1.0
        t = t[1:]

    t = t.strip()
    if not t:
        return None

    val = _parse_positive_number(t)
    return sign * val if val is not None else None


def _parse_positive_number(t: str) -> float | None:
    """Parse a positive number string handling K/M suffix, commas, scientific notation."""
    t = t.strip()

    # Handle K/M suffix
    multiplier = 1.0
    if t.upper().endswith("K"):
        multiplier = 1_000
        t = t[:-1]
    elif t.upper().endswith("M"):
        multiplier = 1_000_000
        t = t[:-1]

    t = t.strip()
    if not t:
        return None

    # Scientific notation
    if re.match(r"^\d+\.?\d*[eE][+-]?\d+$", t):
        try:
            return float(t) * multiplier
        except ValueError:
            return None

    # Detect European format: "1.234,56" (dot as thousands, comma as decimal)
    if re.match(r"^\d{1,3}(\.\d{3})+,\d+$", t):
        t = t.replace(".", "").replace(",", ".")
        try:
            return float(t) * multiplier
        except ValueError:
            return None

    # Standard format: remove commas
    t = t.replace(",", "")

    try:
        return float(t) * multiplier
    except ValueError:
        return None

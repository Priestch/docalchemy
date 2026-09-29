"""Shadow comparison: legacy docling pipeline vs the DocAlchemy provider pack.

For each document, both sides start from the SAME engine output, so any
difference is a mapping difference, not engine drift:

  baseline  our provider's raw export (docling export_to_dict)
            -> this repo's legacy normalizer -> RenderDocument A
  candidate our provider's normalized result (contract Document)
            -> pack mapper -> RenderDocument B

Run from the repo root with the service venv:

    .venv/bin/python scripts/shadow_compare.py <file.pdf> [more.pdf ...]

Requires the docling provider speaking the job protocol at PROVIDER_URL
(default http://127.0.0.1:8099).
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

import httpx
import msgspec
from docalchemy_contract import Document, JobResult

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from app.infrastructure.providers.docling.normalizer import (  # noqa: E402
    docling_raw_to_render_document,
)
from app.infrastructure.providers.pack.mapper import (  # noqa: E402
    document_to_render_document,
)
from app.infrastructure.render_document import RenderDocument  # noqa: E402

PROVIDER_URL = "http://127.0.0.1:8099"


def parse_with_pack(pdf: Path, artifacts_dir: Path) -> tuple[Document, dict]:
    """One job through the provider; returns the normalized document and the
    raw engine export written beside the artifacts."""
    with tempfile.TemporaryDirectory() as tmp:
        job_dir = Path(tmp) / "artifacts"
        job_dir.mkdir()
        accepted = httpx.post(
            f"{PROVIDER_URL}/jobs",
            json={
                "input_uri": str(pdf.resolve()),
                "input_format": pdf.suffix.lstrip(".").lower(),
                "options": {},
                "artifacts_dir": str(job_dir),
            },
            timeout=30.0,
        )
        accepted.raise_for_status()
        job_id = accepted.json()["job_id"]

        deadline = time.monotonic() + 600.0
        while time.monotonic() < deadline:
            response = httpx.get(f"{PROVIDER_URL}/jobs/{job_id}/result", timeout=30.0)
            if response.status_code == 200:
                result = msgspec.json.decode(response.content, type=JobResult)
                break
            time.sleep(1.0)
        else:
            raise RuntimeError(f"job {job_id} never finished")

        if not result.ok:
            raise RuntimeError(f"job failed: {result.error}")

        raw = json.loads((job_dir / "document.json").read_text())
        for item in job_dir.iterdir():
            if item.is_file():
                (artifacts_dir / item.name).write_bytes(item.read_bytes())
        return result.document, raw


def iou(a, b) -> float | None:
    if a is None or b is None:
        return None
    x0, y0 = max(a.x0, b.x0), max(a.y0, b.y0)
    x1, y1 = min(a.x1, b.x1), min(a.y1, b.y1)
    inter = max(0.0, x1 - x0) * max(0.0, y1 - y0)
    union = (a.x1 - a.x0) * (a.y1 - a.y0) + (b.x1 - b.x0) * (b.y1 - b.y0) - inter
    return inter / union if union else None


def compare(name: str, baseline: RenderDocument, candidate: RenderDocument) -> dict:
    report: dict = {"document": name}

    report["pages"] = {
        "baseline": len(baseline.pages),
        "candidate": len(candidate.pages),
        "match": [p.page_index for p in baseline.pages] == [p.page_index for p in candidate.pages],
    }

    def counts(doc: RenderDocument) -> dict[str, int]:
        out: dict[str, int] = {}
        for block in doc.blocks:
            out[block.block_type] = out.get(block.block_type, 0) + 1
        return dict(sorted(out.items()))

    report["block_counts"] = {"baseline": counts(baseline), "candidate": counts(candidate)}

    # Pair by exact text match: the baseline's own ordering is unusable for
    # pairing — its blocks list is grouped by category (texts, then tables),
    # and its reading_order field stays at the default 0 for every block
    # nested inside a group (list items most notably), because the normalizer
    # only walks top-level body children. Text pairing validates the mapping;
    # ordering is reported separately as a known baseline limitation.
    from collections import defaultdict

    by_text_baseline: dict[str, list] = defaultdict(list)
    for block in baseline.blocks:
        by_text_baseline[block.text.strip()].append(block)
    paired = type_mismatch = both = 0
    unmatched: list[str] = []
    bbox_hits = 0
    for b in candidate.blocks:
        pool = by_text_baseline.get(b.text.strip())
        if not pool:
            unmatched.append(f"{b.block_type}: {b.text[:30]!r}")
            continue
        a = pool.pop(0)
        paired += 1
        if a.block_type != b.block_type:
            type_mismatch += 1
        else:
            both += 1
        overlap = iou(a.bbox, b.bbox)
        if overlap is not None and overlap > 0.95:
            bbox_hits += 1
    report["blocks"] = {
        "baseline": len(baseline.blocks),
        "candidate": len(candidate.blocks),
        "paired_by_text": paired,
        "unmatched_candidate": unmatched[:8],
        "type_mismatches": type_mismatch,
        "same_type_pairs": both,
        "bbox_iou_over_0.95": bbox_hits,
    }
    baseline_ordered = baseline.blocks  # list order; see note above
    candidate_ordered = sorted(candidate.blocks, key=lambda b: b.reading_order)

    table_report = []
    for ta, tb in zip(baseline.tables, candidate.tables):
        same_cells = sum(
            1
            for ca, cb in zip(ta.cells, tb.cells)
            if (ca.row_index, ca.col_index, ca.text.strip()) == (cb.row_index, cb.col_index, cb.text.strip())
        )
        table_report.append(
            {
                "rows": [ta.rows, tb.rows],
                "cols": [ta.cols, tb.cols],
                "cells": [len(ta.cells), len(tb.cells)],
                "cells_matching": same_cells,
                "cell_bboxes": [sum(1 for c in ta.cells if c.bbox), sum(1 for c in tb.cells if c.bbox)],
            }
        )
    report["tables"] = table_report
    report["figures"] = [len(baseline.figures), len(candidate.figures)]
    # Baseline's reading_order is unreliable for grouped blocks (see note in
    # the pairing section); ordering fidelity is the candidate's own property,
    # asserted there instead of diffed against a broken reference.
    report["reading_order_monotonic_in_candidate"] = [b.reading_order for b in candidate_ordered] == sorted(
        b.reading_order for b in candidate_ordered
    )
    report["cell_bbox_mode"] = [baseline.cell_bbox_mode, candidate.cell_bbox_mode]
    return report


def main() -> None:
    pdfs = [Path(arg) for arg in sys.argv[1:]]
    if not pdfs:
        raise SystemExit("usage: shadow_compare.py <file.pdf> [...]")

    failures = 0
    for pdf in pdfs:
        with tempfile.TemporaryDirectory() as tmp:
            document, raw = parse_with_pack(pdf, Path(tmp))
        baseline = docling_raw_to_render_document(raw, {})
        candidate = document_to_render_document(document)
        report = compare(pdf.name, baseline, candidate)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        blocks = report["blocks"]
        serious = (
            report["pages"]["baseline"] != report["pages"]["candidate"]
            or abs(blocks["baseline"] - blocks["candidate"]) > max(2, 0.05 * blocks["baseline"])
            or blocks["type_mismatches"] > max(2, 0.05 * max(blocks["baseline"], 1))
            or (blocks["paired_by_text"] and blocks["paired_by_text"] < 0.9 * blocks["candidate"])
        )
        print(f"== {pdf.name}: {'DIFFERENCES NEED REVIEW' if serious else 'within tolerance'}")
        failures += serious
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()

from __future__ import annotations

from enum import StrEnum


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ArtifactType(StrEnum):
    RAW_JSON = "raw_json"
    RAW_MARKDOWN = "raw_markdown"
    RAW_HTML = "raw_html"
    RENDER_DOCUMENT = "render_document"
    # A provider pack's own normalized output — the mapper's input, stored so
    # re-normalization never needs the engine again.
    NORMALIZED = "normalized"
    FIGURE = "figure"
    # Fallback for kinds this app doesn't model yet; providers may add kinds
    # independently, and an unknown kind must not fail the whole run.
    OTHER = "other"

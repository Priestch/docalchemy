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

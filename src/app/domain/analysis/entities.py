from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.analysis.value_objects import AnalysisStatus, ArtifactType


class AnalysisRun(BaseModel):
    id: UUID
    source_document_id: UUID
    provider_id: str
    provider_version: str = ""
    status: AnalysisStatus = AnalysisStatus.PENDING
    requested_config: dict = Field(default_factory=dict)
    runtime_metadata: dict | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    def mark_running(self) -> None:
        if self.status not in (AnalysisStatus.QUEUED, AnalysisStatus.PENDING):
            msg = f"Cannot transition from {self.status} to running"
            raise ValueError(msg)
        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.now(tz=self.started_at.tzinfo) if self.started_at else datetime.now()

    def mark_succeeded(self, runtime_metadata: dict | None = None) -> None:
        if self.status != AnalysisStatus.RUNNING:
            msg = f"Cannot transition from {self.status} to success"
            raise ValueError(msg)
        self.status = AnalysisStatus.SUCCESS
        self.finished_at = datetime.now()
        if runtime_metadata:
            self.runtime_metadata = runtime_metadata

    def mark_failed(self, error_code: str, error_message: str) -> None:
        if self.status not in (AnalysisStatus.RUNNING, AnalysisStatus.QUEUED, AnalysisStatus.PENDING):
            msg = f"Cannot transition from {self.status} to failed"
            raise ValueError(msg)
        self.status = AnalysisStatus.FAILED
        self.finished_at = datetime.now()
        self.error_code = error_code
        self.error_message = error_message

    def can_retry(self) -> bool:
        return self.status in (AnalysisStatus.FAILED, AnalysisStatus.CANCELLED)


class AnalysisArtifact(BaseModel):
    id: UUID
    analysis_run_id: UUID
    artifact_type: ArtifactType
    format: str
    storage_key: str
    created_at: datetime

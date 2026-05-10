from __future__ import annotations

from datetime import datetime, timezone

import pytest
from uuid import uuid4

from app.domain.analysis.entities import AnalysisRun
from app.domain.analysis.value_objects import AnalysisStatus


def _make_run(status: AnalysisStatus = AnalysisStatus.PENDING) -> AnalysisRun:
    return AnalysisRun(
        id=uuid4(),
        source_document_id=uuid4(),
        provider_id="docling",
        status=status,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


class TestAnalysisRunStateTransitions:
    def test_pending_to_running(self) -> None:
        run = _make_run(AnalysisStatus.PENDING)
        run.mark_running()
        assert run.status == AnalysisStatus.RUNNING

    def test_queued_to_running(self) -> None:
        run = _make_run(AnalysisStatus.QUEUED)
        run.mark_running()
        assert run.status == AnalysisStatus.RUNNING

    def test_running_to_success(self) -> None:
        run = _make_run(AnalysisStatus.RUNNING)
        run.mark_succeeded({"processing_time_seconds": 5.0})
        assert run.status == AnalysisStatus.SUCCESS
        assert run.finished_at is not None
        assert run.runtime_metadata == {"processing_time_seconds": 5.0}

    def test_running_to_failed(self) -> None:
        run = _make_run(AnalysisStatus.RUNNING)
        run.mark_failed("TIMEOUT", "Processing timed out")
        assert run.status == AnalysisStatus.FAILED
        assert run.finished_at is not None
        assert run.error_code == "TIMEOUT"
        assert run.error_message == "Processing timed out"

    def test_queued_to_failed(self) -> None:
        run = _make_run(AnalysisStatus.QUEUED)
        run.mark_failed("DISPATCH_ERROR", "Worker unreachable")
        assert run.status == AnalysisStatus.FAILED

    def test_pending_to_failed(self) -> None:
        run = _make_run(AnalysisStatus.PENDING)
        run.mark_failed("SETUP_ERROR", "Config invalid")
        assert run.status == AnalysisStatus.FAILED


class TestAnalysisRunInvalidTransitions:
    @pytest.mark.parametrize("status", [AnalysisStatus.SUCCESS, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED])
    def test_cannot_transition_to_running_from_terminal(self, status: AnalysisStatus) -> None:
        run = _make_run(status)
        with pytest.raises(ValueError, match="Cannot transition"):
            run.mark_running()

    @pytest.mark.parametrize("status", [AnalysisStatus.PENDING, AnalysisStatus.SUCCESS, AnalysisStatus.CANCELLED])
    def test_cannot_transition_to_success_from_invalid(self, status: AnalysisStatus) -> None:
        run = _make_run(status)
        with pytest.raises(ValueError, match="Cannot transition"):
            run.mark_succeeded()

    @pytest.mark.parametrize("status", [AnalysisStatus.SUCCESS, AnalysisStatus.CANCELLED])
    def test_cannot_transition_to_failed_from_terminal(self, status: AnalysisStatus) -> None:
        run = _make_run(status)
        with pytest.raises(ValueError, match="Cannot transition"):
            run.mark_failed("X", "Y")


class TestAnalysisRunRetry:
    def test_can_retry_failed(self) -> None:
        run = _make_run(AnalysisStatus.FAILED)
        assert run.can_retry() is True

    def test_can_retry_cancelled(self) -> None:
        run = _make_run(AnalysisStatus.CANCELLED)
        assert run.can_retry() is True

    @pytest.mark.parametrize("status", [AnalysisStatus.PENDING, AnalysisStatus.QUEUED, AnalysisStatus.RUNNING, AnalysisStatus.SUCCESS])
    def test_cannot_retry_non_terminal(self, status: AnalysisStatus) -> None:
        run = _make_run(status)
        assert run.can_retry() is False

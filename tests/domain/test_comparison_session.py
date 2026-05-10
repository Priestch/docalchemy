from __future__ import annotations

from datetime import datetime, timezone

import pytest
from uuid import uuid4

from app.domain.comparison.entities import ComparisonSession


class TestComparisonSession:
    def test_valid_session_with_two_runs(self) -> None:
        doc_id = uuid4()
        session = ComparisonSession(
            id=uuid4(),
            source_document_id=doc_id,
            analysis_run_ids=[uuid4(), uuid4()],
            created_at=datetime.now(tz=timezone.utc),
        )
        assert len(session.analysis_run_ids) == 2

    def test_session_with_many_runs(self) -> None:
        session = ComparisonSession(
            id=uuid4(),
            source_document_id=uuid4(),
            analysis_run_ids=[uuid4() for _ in range(5)],
            created_at=datetime.now(tz=timezone.utc),
        )
        assert len(session.analysis_run_ids) == 5

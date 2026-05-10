from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.use_cases.create_comparison_session import CreateComparisonSession
from app.domain.analysis.entities import AnalysisRun
from app.domain.analysis.value_objects import AnalysisStatus
from tests.fakes.fake_uow import FakeAnalysisUnitOfWork, FakeComparisonUnitOfWork


def _make_run(
    source_document_id: str | None = None,
    status: AnalysisStatus = AnalysisStatus.SUCCESS,
) -> AnalysisRun:
    return AnalysisRun(
        id=uuid4(),
        source_document_id=source_document_id or uuid4(),
        provider_id="docling",
        status=status,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


class TestCreateComparisonSession:
    def test_valid_comparison_with_two_successful_runs(self) -> None:
        async def _test() -> None:
            doc_id = uuid4()
            run1 = _make_run(source_document_id=doc_id)
            run2 = _make_run(source_document_id=doc_id)

            analysis_uow = FakeAnalysisUnitOfWork()
            await analysis_uow.runs.add(run1)
            await analysis_uow.runs.add(run2)

            comparison_uow = FakeComparisonUnitOfWork()
            use_case = CreateComparisonSession(
                comparison_uow=comparison_uow,
                analysis_uow=analysis_uow,
            )

            result = await use_case.execute(
                source_document_id=str(doc_id),
                analysis_run_ids=[str(run1.id), str(run2.id)],
            )

            assert result.source_document_id == doc_id
            assert len(result.analysis_run_ids) == 2
            assert comparison_uow._committed

        asyncio.run(_test())

    def test_rejects_fewer_than_two_runs(self) -> None:
        async def _test() -> None:
            analysis_uow = FakeAnalysisUnitOfWork()
            comparison_uow = FakeComparisonUnitOfWork()
            use_case = CreateComparisonSession(
                comparison_uow=comparison_uow,
                analysis_uow=analysis_uow,
            )

            with pytest.raises(ValueError, match="At least 2 runs"):
                await use_case.execute(
                    source_document_id=str(uuid4()),
                    analysis_run_ids=[str(uuid4())],
                )

        asyncio.run(_test())

    def test_rejects_runs_from_different_documents(self) -> None:
        async def _test() -> None:
            doc_id = uuid4()
            run1 = _make_run(source_document_id=doc_id)
            run2 = _make_run(source_document_id=uuid4())

            analysis_uow = FakeAnalysisUnitOfWork()
            await analysis_uow.runs.add(run1)
            await analysis_uow.runs.add(run2)

            comparison_uow = FakeComparisonUnitOfWork()
            use_case = CreateComparisonSession(
                comparison_uow=comparison_uow,
                analysis_uow=analysis_uow,
            )

            with pytest.raises(ValueError, match="same source document"):
                await use_case.execute(
                    source_document_id=str(doc_id),
                    analysis_run_ids=[str(run1.id), str(run2.id)],
                )

        asyncio.run(_test())

    def test_rejects_non_successful_runs(self) -> None:
        async def _test() -> None:
            doc_id = uuid4()
            run1 = _make_run(source_document_id=doc_id, status=AnalysisStatus.SUCCESS)
            run2 = _make_run(source_document_id=doc_id, status=AnalysisStatus.FAILED)

            analysis_uow = FakeAnalysisUnitOfWork()
            await analysis_uow.runs.add(run1)
            await analysis_uow.runs.add(run2)

            comparison_uow = FakeComparisonUnitOfWork()
            use_case = CreateComparisonSession(
                comparison_uow=comparison_uow,
                analysis_uow=analysis_uow,
            )

            with pytest.raises(ValueError, match="expected success"):
                await use_case.execute(
                    source_document_id=str(doc_id),
                    analysis_run_ids=[str(run1.id), str(run2.id)],
                )

        asyncio.run(_test())

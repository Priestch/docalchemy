"""comparison tables only

Document/analysis domain tables (source_document, analysis_run,
analysis_artifact, render_block, render_figure) are owned by
docalchemy-gateway and its own migration chain (version table
gateway_ddl_version). This chain owns only the app's scenario tables.

Revision ID: 0001_new_domain
Revises:
Create Date: 2025-01-01 00:00:00.000000+00:00

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade"]

# revision identifiers, used by Alembic.
revision = "0001_new_domain"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            op.create_table(
                "comparison_session",
                sa.Column("id", sa.Uuid(), nullable=False),
                sa.Column("source_document_id", sa.Uuid(), nullable=False),
                sa.Column("created_by", sa.String(length=255), nullable=True),
                sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
                sa.PrimaryKeyConstraint("id"),
                sa.ForeignKeyConstraint(["source_document_id"], ["source_document.id"]),
            )

            op.create_table(
                "comparison_session_runs",
                sa.Column("comparison_session_id", sa.Uuid(), nullable=False),
                sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
                sa.PrimaryKeyConstraint("comparison_session_id", "analysis_run_id"),
                sa.ForeignKeyConstraint(["comparison_session_id"], ["comparison_session.id"]),
                sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_run.id"]),
            )


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            op.drop_table("comparison_session_runs")
            op.drop_table("comparison_session")

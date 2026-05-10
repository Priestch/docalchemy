"""add source_document analysis_run analysis_artifact comparison_session

Revision ID: 0001_new_domain
Revises: 52cfe391ad53
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
down_revision = "52cfe391ad53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            op.create_table(
                "source_document",
                sa.Column("id", sa.Uuid(), nullable=False),
                sa.Column("name", sa.String(length=255), nullable=False),
                sa.Column("mime_type", sa.String(length=100), nullable=False),
                sa.Column("size_bytes", sa.BigInteger(), nullable=False),
                sa.Column("storage_key", sa.String(length=64), nullable=False),
                sa.Column("checksum", sa.String(length=32), nullable=False),
                sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
                sa.Column("page_dimensions", sa.JSON(), nullable=False, server_default="[]"),
                sa.Column("uploaded_by", sa.String(length=255), nullable=True),
                sa.Column("slug", sa.String(length=100), nullable=True),
                sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
                sa.PrimaryKeyConstraint("id"),
                sa.UniqueConstraint("storage_key"),
                sa.UniqueConstraint("slug"),
            )

            op.create_table(
                "analysis_run",
                sa.Column("id", sa.Uuid(), nullable=False),
                sa.Column("source_document_id", sa.Uuid(), nullable=False),
                sa.Column("provider_id", sa.String(length=50), nullable=False),
                sa.Column("provider_version", sa.String(length=20), nullable=False, server_default=""),
                sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
                sa.Column("requested_config", sa.JSON(), nullable=False, server_default="{}"),
                sa.Column("runtime_metadata", sa.JSON(), nullable=True),
                sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
                sa.Column("error_code", sa.String(length=50), nullable=True),
                sa.Column("error_message", sa.Text(), nullable=True),
                sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
                sa.PrimaryKeyConstraint("id"),
                sa.ForeignKeyConstraint(["source_document_id"], ["source_document.id"]),
            )

            op.create_table(
                "analysis_artifact",
                sa.Column("id", sa.Uuid(), nullable=False),
                sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
                sa.Column("artifact_type", sa.String(length=30), nullable=False),
                sa.Column("format", sa.String(length=10), nullable=False),
                sa.Column("storage_key", sa.String(length=64), nullable=False),
                sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
                sa.PrimaryKeyConstraint("id"),
                sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_run.id"]),
            )

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
            op.drop_table("analysis_artifact")
            op.drop_table("analysis_run")
            op.drop_table("source_document")

# type: ignore
"""Create project table

Revision ID: cdd98f5395d7
Revises: 
Create Date: 2024-07-20 00:18:32.962056+00:00

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import EncryptedString, EncryptedText, GUID, ORA_JSONB, DateTimeUTC
from sqlalchemy import Text  # noqa: F401

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText

# revision identifiers, used by Alembic.
revision = 'cdd98f5395d7'
down_revision = None
branch_labels = None
depends_on = None

table_name = "project"


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    op.create_table(table_name,
                    sa.Column("id", sa.GUID(length=16), nullable=False),
                    sa.Column('sa_orm_sentinel', sa.Integer(), nullable=True),
                    sa.Column("name", sa.String(length=255), nullable=False),
                    sa.Column("store_key", sa.String(length=40), nullable=False),
                    sa.Column("owner", sa.String(length=64), nullable=False),
                    sa.Column("status", sa.Integer(), nullable=True, server_default=sa.text("0")),
                    sa.Column('created_at', sa.DateTimeUTC(timezone=True), nullable=False),
                    sa.Column('updated_at', sa.DateTimeUTC(timezone=True), nullable=False),
                    sa.PrimaryKeyConstraint("id", name=op.f("pk_project")),
                    )

    op.create_index("ix_project_owner_status", table_name, ["owner", "status"], unique=False)


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_table(table_name)


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""

"""Initial schema - all 22 tables of Vidyalaya AI.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-31

The initial revision creates the schema from the SQLAlchemy metadata, which
keeps this file short and guarantees it matches ``app/models`` exactly. Every
later change should be generated with:

    alembic revision --autogenerate -m "describe the change"

which produces ordinary op.create_table / op.add_column migrations.
"""
from __future__ import annotations

from alembic import op

from app.models import Base  # registers every table on Base.metadata

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

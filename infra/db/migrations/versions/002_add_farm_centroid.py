"""Add centroid coordinates to farms table

Revision ID: 002_add_farm_centroid
Revises: 001_initial_schema
Create Date: 2026-11-06 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_add_farm_centroid"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("farms", sa.Column("centroid_latitude", sa.Float(), nullable=True))
    op.add_column("farms", sa.Column("centroid_longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("farms", "centroid_longitude")
    op.drop_column("farms", "centroid_latitude")

"""add map obstacle geometry

Revision ID: 0005_map_obstacles
Revises: 0004_map_backgrounds
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_map_obstacles"
down_revision: str | None = "0004_map_backgrounds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def json_type() -> sa.JSON:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "map_obstacles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("points", json_type(), nullable=False),
        sa.Column("safety_margin", sa.Float(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["map_id"], ["maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_map_obstacles_map_id", "map_obstacles", ["map_id"])


def downgrade() -> None:
    op.drop_index("ix_map_obstacles_map_id", table_name="map_obstacles")
    op.drop_table("map_obstacles")

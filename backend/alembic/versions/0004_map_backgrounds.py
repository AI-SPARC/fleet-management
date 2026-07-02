"""add calibrated map backgrounds

Revision ID: 0004_map_backgrounds
Revises: 0003_mission_orders
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_map_backgrounds"
down_revision: str | None = "0003_mission_orders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "map_backgrounds",
        sa.Column("map_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("meters_per_pixel", sa.Float(), nullable=True),
        sa.Column("origin_pixel_x", sa.Float(), nullable=True),
        sa.Column("origin_pixel_y", sa.Float(), nullable=True),
        sa.Column("rotation_degrees", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["map_id"], ["maps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("map_id"),
    )


def downgrade() -> None:
    op.drop_table("map_backgrounds")

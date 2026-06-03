"""add extended physical metrics columns to run index rows"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_run_index_extended_fields"
down_revision = ("0005_resolver_cases", "0005_run_index_rows")
branch_labels = None
depends_on = None

_COLUMNS = (
    "instance_area_um2",
    "stdcell_area_um2",
    "stdcell_count",
    "core_area_um2",
    "utilization_pct",
)


def upgrade() -> None:
    for column_name in _COLUMNS:
        op.add_column(
            "run_index_rows",
            sa.Column(column_name, sa.String(length=64), nullable=False, server_default=""),
        )


def downgrade() -> None:
    for column_name in reversed(_COLUMNS):
        op.drop_column("run_index_rows", column_name)

"""fix active worker lease partial-index predicate"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0007_fix_active_lease_index"
down_revision = "0006_run_index_extended_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("uq_worker_leases_active_work_item", table_name="worker_leases")
    op.create_index(
        "uq_worker_leases_active_work_item",
        "worker_leases",
        ["work_item_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index("uq_worker_leases_active_work_item", table_name="worker_leases")
    op.create_index(
        "uq_worker_leases_active_work_item",
        "worker_leases",
        ["work_item_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )

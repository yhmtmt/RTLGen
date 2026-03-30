"""add multi-evaluator assignment metadata"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_multi_evaluator_assignment"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("work_items", sa.Column("assigned_machine_key", sa.String(length=255), nullable=True))
    op.create_index(
        "ix_work_items_assigned_machine_state",
        "work_items",
        ["assigned_machine_key", "state", "priority", "created_at"],
    )
    op.add_column("worker_machines", sa.Column("role", sa.String(length=64), nullable=False, server_default="evaluator"))
    op.add_column("worker_machines", sa.Column("slot_capacity", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("worker_machines", "slot_capacity")
    op.drop_column("worker_machines", "role")
    op.drop_index("ix_work_items_assigned_machine_state", table_name="work_items")
    op.drop_column("work_items", "assigned_machine_key")

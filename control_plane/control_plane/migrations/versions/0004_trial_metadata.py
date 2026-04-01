"""add trial metadata and failure fields"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_trial_metadata"
down_revision = "0003_dispatch_pending_state"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.add_column("work_items", sa.Column("trial_policy_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("runs", sa.Column("trial_index", sa.Integer(), nullable=True))
    op.add_column("runs", sa.Column("seed", sa.Integer(), nullable=True))
    op.add_column("runs", sa.Column("trial_group_key", sa.String(length=255), nullable=True))
    op.add_column("runs", sa.Column("flow_variant", sa.String(length=128), nullable=True))
    op.add_column("runs", sa.Column("scheduler_variant", sa.String(length=128), nullable=True))
    op.add_column("runs", sa.Column("failure_stage", sa.String(length=128), nullable=True))
    op.add_column("runs", sa.Column("failure_category", sa.String(length=128), nullable=True))
    op.add_column("runs", sa.Column("failure_signature", sa.String(length=255), nullable=True))
    op.add_column("runs", sa.Column("runtime_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "runtime_seconds")
    op.drop_column("runs", "failure_signature")
    op.drop_column("runs", "failure_category")
    op.drop_column("runs", "failure_stage")
    op.drop_column("runs", "scheduler_variant")
    op.drop_column("runs", "flow_variant")
    op.drop_column("runs", "trial_group_key")
    op.drop_column("runs", "seed")
    op.drop_column("runs", "trial_index")
    op.drop_column("work_items", "trial_policy_json")

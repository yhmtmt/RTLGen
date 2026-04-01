"""expand work item state enum width for dispatch_pending"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_dispatch_pending_state"
down_revision = "0002_multi_evaluator_assignment"
branch_labels = None
depends_on = None

work_item_state_enum = sa.Enum(
    "draft",
    "dispatch_pending",
    "ready",
    "leased",
    "running",
    "artifact_sync",
    "awaiting_review",
    "merged",
    "failed",
    "blocked",
    "superseded",
    name="workitemstate",
    native_enum=False,
    length=32,
)


def upgrade() -> None:
    op.alter_column(
        "work_items",
        "state",
        existing_type=sa.String(length=15),
        type_=work_item_state_enum,
        existing_nullable=False,
        existing_server_default="draft",
        postgresql_using="state::varchar(32)",
    )


def downgrade() -> None:
    legacy_state_enum = sa.Enum(
        "draft",
        "ready",
        "leased",
        "running",
        "artifact_sync",
        "awaiting_review",
        "merged",
        "failed",
        "blocked",
        "superseded",
        name="workitemstate",
        native_enum=False,
        length=15,
    )
    op.execute("UPDATE work_items SET state = 'ready' WHERE state = 'dispatch_pending'")
    op.alter_column(
        "work_items",
        "state",
        existing_type=work_item_state_enum,
        type_=legacy_state_enum,
        existing_nullable=False,
        existing_server_default="draft",
        postgresql_using="state::varchar(15)",
    )

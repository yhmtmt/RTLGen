"""add resolver case tracking tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_resolver_cases"
down_revision = "0004_trial_metadata"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "resolver_cases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint", sa.String(length=255), nullable=False),
        sa.Column("failure_class", sa.String(length=128), nullable=False),
        sa.Column("owner", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="medium"),
        sa.Column("issue_number", sa.Integer(), nullable=True),
        sa.Column("first_item_id", sa.String(length=255), nullable=True),
        sa.Column("latest_item_id", sa.String(length=255), nullable=True),
        sa.Column("first_run_key", sa.String(length=255), nullable=True),
        sa.Column("latest_run_key", sa.String(length=255), nullable=True),
        sa.Column("machine_key", sa.String(length=255), nullable=True),
        sa.Column("source_commit", sa.String(length=64), nullable=True),
        sa.Column("repo_root", sa.Text(), nullable=True),
        sa.Column("evidence_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("resolution_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("last_evidence_hash", sa.String(length=64), nullable=True),
        sa.Column("last_attempted_evidence_hash", sa.String(length=64), nullable=True),
        sa.Column("last_failure_hash", sa.String(length=64), nullable=True),
        sa.Column("last_action_type", sa.String(length=64), nullable=True),
        sa.Column("last_action_status", sa.String(length=32), nullable=True),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resolver_cases")),
    )
    op.create_index("ix_resolver_cases_status_created_at", "resolver_cases", ["status", "created_at"], unique=False)
    op.create_index(
        "ix_resolver_cases_owner_status_created_at",
        "resolver_cases",
        ["owner", "status", "created_at"],
        unique=False,
    )
    op.create_index("ix_resolver_cases_fingerprint_status", "resolver_cases", ["fingerprint", "status"], unique=False)

    op.create_table(
        "resolver_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["resolver_cases.id"], name=op.f("fk_resolver_observations_case_id_resolver_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resolver_observations")),
    )
    op.create_index(
        "ix_resolver_observations_case_created_at",
        "resolver_observations",
        ["case_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_resolver_observations_source_kind_created_at",
        "resolver_observations",
        ["source", "kind", "created_at"],
        unique=False,
    )

    op.create_table(
        "resolver_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=36), nullable=False),
        sa.Column("actor", sa.String(length=32), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("action_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_index", sa.Integer(), nullable=False),
        sa.Column("evidence_hash", sa.String(length=64), nullable=True),
        sa.Column("failure_hash", sa.String(length=64), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_json", json_type, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["case_id"], ["resolver_cases.id"], name=op.f("fk_resolver_actions_case_id_resolver_cases")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resolver_actions")),
        sa.UniqueConstraint("idempotency_key", name="uq_resolver_actions_idempotency_key"),
    )
    op.create_index(
        "ix_resolver_actions_case_created_at",
        "resolver_actions",
        ["case_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_resolver_actions_action_status_created_at",
        "resolver_actions",
        ["action_key", "status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resolver_actions_action_status_created_at", table_name="resolver_actions")
    op.drop_index("ix_resolver_actions_case_created_at", table_name="resolver_actions")
    op.drop_table("resolver_actions")

    op.drop_index("ix_resolver_observations_source_kind_created_at", table_name="resolver_observations")
    op.drop_index("ix_resolver_observations_case_created_at", table_name="resolver_observations")
    op.drop_table("resolver_observations")

    op.drop_index("ix_resolver_cases_fingerprint_status", table_name="resolver_cases")
    op.drop_index("ix_resolver_cases_owner_status_created_at", table_name="resolver_cases")
    op.drop_index("ix_resolver_cases_status_created_at", table_name="resolver_cases")
    op.drop_table("resolver_cases")

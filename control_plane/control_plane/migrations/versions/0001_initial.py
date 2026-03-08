"""initial control plane schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

layer_enum = sa.Enum("layer1", "layer2", "meta", name="layername", native_enum=False)
flow_enum = sa.Enum("openroad", name="flowname", native_enum=False)
work_item_state_enum = sa.Enum(
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
)
lease_status_enum = sa.Enum("active", "expired", "released", "revoked", name="leasestatus", native_enum=False)
executor_type_enum = sa.Enum(
    "internal_worker",
    "external_pr",
    "agent_assisted_worker",
    name="executortype",
    native_enum=False,
)
run_status_enum = sa.Enum(
    "starting",
    "running",
    "succeeded",
    "failed",
    "canceled",
    "timed_out",
    name="runstatus",
    native_enum=False,
)
artifact_storage_mode_enum = sa.Enum("transient", "repo", name="artifactstoragemode", native_enum=False)
github_link_state_enum = sa.Enum(
    "none",
    "branch_created",
    "pr_open",
    "pr_merged",
    "pr_closed",
    name="githublinkstate",
    native_enum=False,
)
queue_reconciliation_direction_enum = sa.Enum("import", "export", name="queuereconciliationdirection", native_enum=False)
queue_reconciliation_status_enum = sa.Enum(
    "applied",
    "skipped",
    "conflict",
    "error",
    name="queuereconciliationstatus",
    native_enum=False,
)
json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")
uuid_type = sa.String(length=36)


def upgrade() -> None:
    op.create_table(
        "task_requests",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("request_key", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("requested_by", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("layer", layer_enum, nullable=False),
        sa.Column("flow", flow_enum, nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("request_payload", json_type, nullable=False),
        sa.Column("source_commit", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_task_requests"),
        sa.UniqueConstraint("request_key", name="uq_task_requests_request_key"),
    )
    op.create_index("ix_task_requests_layer_flow_created_at", "task_requests", ["layer", "flow", "created_at"])

    op.create_table(
        "worker_machines",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("machine_key", sa.String(length=255), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("executor_kind", sa.String(length=64), nullable=False),
        sa.Column("capabilities", json_type, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_worker_machines"),
        sa.UniqueConstraint("machine_key", name="uq_worker_machines_machine_key"),
    )
    op.create_index(
        "ix_worker_machines_capabilities",
        "worker_machines",
        ["capabilities"],
        postgresql_using="gin",
    )

    op.create_table(
        "work_items",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("work_item_key", sa.String(length=255), nullable=False),
        sa.Column("task_request_id", uuid_type, nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("layer", layer_enum, nullable=False),
        sa.Column("flow", flow_enum, nullable=False),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("state", work_item_state_enum, nullable=False, server_default="draft"),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("source_mode", sa.String(length=64), nullable=True),
        sa.Column("input_manifest", json_type, nullable=False),
        sa.Column("command_manifest", json_type, nullable=False),
        sa.Column("expected_outputs", json_type, nullable=False),
        sa.Column("acceptance_rules", json_type, nullable=False),
        sa.Column("queue_snapshot_path", sa.Text(), nullable=True),
        sa.Column("source_commit", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_request_id"], ["task_requests.id"], name="fk_work_items_task_request_id_task_requests"),
        sa.PrimaryKeyConstraint("id", name="pk_work_items"),
        sa.UniqueConstraint("item_id", name="uq_work_items_item_id"),
        sa.UniqueConstraint("work_item_key", name="uq_work_items_work_item_key"),
    )
    op.create_index("ix_work_items_state_priority_created_at", "work_items", ["state", "priority", "created_at"])
    op.create_index("ix_work_items_layer_platform_state", "work_items", ["layer", "platform", "state"])

    op.create_table(
        "worker_leases",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("work_item_id", uuid_type, nullable=False),
        sa.Column("machine_id", uuid_type, nullable=False),
        sa.Column("lease_token", sa.String(length=255), nullable=False),
        sa.Column("status", lease_status_enum, nullable=False, server_default="active"),
        sa.Column("leased_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["machine_id"], ["worker_machines.id"], name="fk_worker_leases_machine_id_worker_machines"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], name="fk_worker_leases_work_item_id_work_items"),
        sa.PrimaryKeyConstraint("id", name="pk_worker_leases"),
        sa.UniqueConstraint("lease_token", name="uq_worker_leases_lease_token"),
    )
    op.create_index("ix_worker_leases_status_expires_at", "worker_leases", ["status", "expires_at"])
    op.create_index("ix_worker_leases_machine_status", "worker_leases", ["machine_id", "status"])
    op.create_index(
        "uq_worker_leases_active_work_item",
        "worker_leases",
        ["work_item_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "runs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("run_key", sa.String(length=255), nullable=False),
        sa.Column("work_item_id", uuid_type, nullable=False),
        sa.Column("lease_id", uuid_type, nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("executor_type", executor_type_enum, nullable=False),
        sa.Column("machine_id", uuid_type, nullable=True),
        sa.Column("container_image", sa.String(length=255), nullable=True),
        sa.Column("checkout_commit", sa.String(length=64), nullable=True),
        sa.Column("branch_name", sa.String(length=255), nullable=True),
        sa.Column("status", run_status_enum, nullable=False, server_default="starting"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("result_payload", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["lease_id"], ["worker_leases.id"], name="fk_runs_lease_id_worker_leases"),
        sa.ForeignKeyConstraint(["machine_id"], ["worker_machines.id"], name="fk_runs_machine_id_worker_machines"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], name="fk_runs_work_item_id_work_items"),
        sa.PrimaryKeyConstraint("id", name="pk_runs"),
        sa.UniqueConstraint("run_key", name="uq_runs_run_key"),
        sa.UniqueConstraint("work_item_id", "attempt", name="uq_runs_work_item_attempt"),
    )
    op.create_index("ix_runs_work_item_attempt", "runs", ["work_item_id", "attempt"])
    op.create_index("ix_runs_status_started_at", "runs", ["status", "started_at"])

    op.create_table(
        "run_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", uuid_type, nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("event_payload", json_type, nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], name="fk_run_events_run_id_runs"),
        sa.PrimaryKeyConstraint("id", name="pk_run_events"),
    )
    op.create_index("ix_run_events_run_id_event_time", "run_events", ["run_id", "event_time"])

    op.create_table(
        "artifacts",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("run_id", uuid_type, nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("storage_mode", artifact_storage_mode_enum, nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("metadata", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], name="fk_artifacts_run_id_runs"),
        sa.PrimaryKeyConstraint("id", name="pk_artifacts"),
    )
    op.create_index("ix_artifacts_run_id_kind", "artifacts", ["run_id", "kind"])
    op.create_index("ix_artifacts_storage_mode_kind", "artifacts", ["storage_mode", "kind"])

    op.create_table(
        "github_links",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("work_item_id", uuid_type, nullable=False),
        sa.Column("run_id", uuid_type, nullable=True),
        sa.Column("repo", sa.String(length=255), nullable=False),
        sa.Column("branch_name", sa.String(length=255), nullable=True),
        sa.Column("pr_number", sa.Integer(), nullable=True),
        sa.Column("pr_url", sa.Text(), nullable=True),
        sa.Column("head_sha", sa.String(length=64), nullable=True),
        sa.Column("base_branch", sa.String(length=255), nullable=True),
        sa.Column("state", github_link_state_enum, nullable=False, server_default="none"),
        sa.Column("metadata", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], name="fk_github_links_run_id_runs"),
        sa.ForeignKeyConstraint(["work_item_id"], ["work_items.id"], name="fk_github_links_work_item_id_work_items"),
        sa.PrimaryKeyConstraint("id", name="pk_github_links"),
    )
    op.create_index("ix_github_links_pr_number", "github_links", ["pr_number"])
    op.create_index("ix_github_links_branch_name", "github_links", ["branch_name"])
    op.create_index("ix_github_links_work_item_state", "github_links", ["work_item_id", "state"])

    op.create_table(
        "queue_reconciliations",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("item_id", sa.String(length=255), nullable=False),
        sa.Column("direction", queue_reconciliation_direction_enum, nullable=False),
        sa.Column("queue_path", sa.Text(), nullable=False),
        sa.Column("queue_sha256", sa.String(length=64), nullable=True),
        sa.Column("db_work_item_id", uuid_type, nullable=True),
        sa.Column("status", queue_reconciliation_status_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["db_work_item_id"], ["work_items.id"], name="fk_queue_reconciliations_db_work_item_id_work_items"),
        sa.PrimaryKeyConstraint("id", name="pk_queue_reconciliations"),
    )
    op.create_index("ix_queue_reconciliations_item_created_at", "queue_reconciliations", ["item_id", "created_at"])
    op.create_index(
        "ix_queue_reconciliations_direction_status_created_at",
        "queue_reconciliations",
        ["direction", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_queue_reconciliations_direction_status_created_at", table_name="queue_reconciliations")
    op.drop_index("ix_queue_reconciliations_item_created_at", table_name="queue_reconciliations")
    op.drop_table("queue_reconciliations")
    op.drop_index("ix_github_links_work_item_state", table_name="github_links")
    op.drop_index("ix_github_links_branch_name", table_name="github_links")
    op.drop_index("ix_github_links_pr_number", table_name="github_links")
    op.drop_table("github_links")
    op.drop_index("ix_artifacts_storage_mode_kind", table_name="artifacts")
    op.drop_index("ix_artifacts_run_id_kind", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_run_events_run_id_event_time", table_name="run_events")
    op.drop_table("run_events")
    op.drop_index("ix_runs_status_started_at", table_name="runs")
    op.drop_index("ix_runs_work_item_attempt", table_name="runs")
    op.drop_table("runs")
    op.drop_index("uq_worker_leases_active_work_item", table_name="worker_leases")
    op.drop_index("ix_worker_leases_machine_status", table_name="worker_leases")
    op.drop_index("ix_worker_leases_status_expires_at", table_name="worker_leases")
    op.drop_table("worker_leases")
    op.drop_index("ix_work_items_layer_platform_state", table_name="work_items")
    op.drop_index("ix_work_items_state_priority_created_at", table_name="work_items")
    op.drop_table("work_items")
    op.drop_index("ix_worker_machines_capabilities", table_name="worker_machines")
    op.drop_table("worker_machines")
    op.drop_index("ix_task_requests_layer_flow_created_at", table_name="task_requests")
    op.drop_table("task_requests")

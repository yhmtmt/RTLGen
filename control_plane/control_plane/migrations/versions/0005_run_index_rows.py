"""add centralized run index rows table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0005_run_index_rows"
down_revision = "0004_trial_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_index_rows",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("index_order", sa.Integer(), nullable=False),
        sa.Column("circuit_type", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("design", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("platform", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("critical_path_ns", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("die_area", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("total_power_mw", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("config_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("param_hash", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("tag", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("result_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("params_json", sa.Text(), nullable=False, server_default=""),
        sa.Column("metrics_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("design_path", sa.Text(), nullable=False, server_default=""),
        sa.Column("sram_area_um2", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("sram_read_energy_pj", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("sram_write_energy_pj", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("sram_max_access_time_ns", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_index_rows")),
    )
    op.create_index(op.f("ix_run_index_rows_order"), "run_index_rows", ["index_order"], unique=False)
    op.create_index(
        op.f("ix_run_index_rows_design_platform"),
        "run_index_rows",
        ["design", "platform"],
        unique=False,
    )
    op.create_index(op.f("ix_run_index_rows_metrics_path"), "run_index_rows", ["metrics_path"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_run_index_rows_metrics_path"), table_name="run_index_rows")
    op.drop_index(op.f("ix_run_index_rows_design_platform"), table_name="run_index_rows")
    op.drop_index(op.f("ix_run_index_rows_order"), table_name="run_index_rows")
    op.drop_table("run_index_rows")

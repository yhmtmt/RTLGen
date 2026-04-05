"""Centralized runs/index.csv rows for analytics and export."""

from __future__ import annotations

from sqlalchemy import Column, Index, Integer, String, Text

from control_plane.models.base import Base, TimestampMixin, uuid_column


class RunIndexRow(TimestampMixin, Base):
    __tablename__ = "run_index_rows"
    __table_args__ = (
        Index("ix_run_index_rows_order", "index_order"),
        Index("ix_run_index_rows_design_platform", "design", "platform"),
        Index("ix_run_index_rows_metrics_path", "metrics_path"),
    )

    id = uuid_column(primary_key=True)
    index_order = Column(Integer, nullable=False)
    circuit_type = Column(String(128), nullable=False, default="")
    design = Column(String(255), nullable=False, default="")
    platform = Column(String(64), nullable=False, default="")
    status = Column(String(64), nullable=False, default="")
    critical_path_ns = Column(String(64), nullable=False, default="")
    die_area = Column(String(64), nullable=False, default="")
    total_power_mw = Column(String(64), nullable=False, default="")
    config_hash = Column(String(128), nullable=False, default="")
    param_hash = Column(String(128), nullable=False, default="")
    tag = Column(String(255), nullable=False, default="")
    result_path = Column(Text, nullable=False, default="")
    params_json = Column(Text, nullable=False, default="")
    metrics_path = Column(Text, nullable=False, default="")
    design_path = Column(Text, nullable=False, default="")
    sram_area_um2 = Column(String(64), nullable=False, default="")
    sram_read_energy_pj = Column(String(64), nullable=False, default="")
    sram_write_energy_pj = Column(String(64), nullable=False, default="")
    sram_max_access_time_ns = Column(String(64), nullable=False, default="")

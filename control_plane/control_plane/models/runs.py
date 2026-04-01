"""Run model."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, TimestampMixin, json_type, uuid_column
from control_plane.models.enums import ExecutorType, RunStatus


class Run(TimestampMixin, Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("work_item_id", "attempt", name="uq_runs_work_item_attempt"),
        Index("ix_runs_work_item_attempt", "work_item_id", "attempt"),
        Index("ix_runs_status_started_at", "status", "started_at"),
    )

    id = uuid_column(primary_key=True)
    run_key = Column(String(255), nullable=False, unique=True)
    work_item_id = uuid_column(foreign_key=ForeignKey("work_items.id"), nullable=False)
    lease_id = uuid_column(foreign_key=ForeignKey("worker_leases.id"), nullable=True)
    attempt = Column(Integer, nullable=False)
    executor_type = Column(Enum(ExecutorType, native_enum=False), nullable=False)
    machine_id = uuid_column(foreign_key=ForeignKey("worker_machines.id"), nullable=True)
    container_image = Column(String(255))
    checkout_commit = Column(String(64))
    branch_name = Column(String(255))
    trial_index = Column(Integer)
    seed = Column(Integer)
    trial_group_key = Column(String(255))
    flow_variant = Column(String(128))
    scheduler_variant = Column(String(128))
    failure_stage = Column(String(128))
    failure_category = Column(String(128))
    failure_signature = Column(String(255))
    runtime_seconds = Column(Float)
    status = Column(Enum(RunStatus, native_enum=False), nullable=False, default=RunStatus.STARTING)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    result_summary = Column(Text, nullable=False, default="")
    result_payload = Column(json_type)

    work_item = relationship("WorkItem", back_populates="runs")
    lease = relationship("WorkerLease", back_populates="runs")
    machine = relationship("WorkerMachine", back_populates="runs")
    events = relationship("RunEvent", back_populates="run")
    artifacts = relationship("Artifact", back_populates="run")
    github_links = relationship("GitHubLink", back_populates="run")

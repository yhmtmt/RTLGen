"""Worker machine model."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, TimestampMixin, json_type, uuid_column


class WorkerMachine(TimestampMixin, Base):
    __tablename__ = "worker_machines"
    __table_args__ = (
        Index("ix_worker_machines_capabilities", "capabilities", postgresql_using="gin"),
    )

    id = uuid_column(primary_key=True)
    machine_key = Column(String(255), nullable=False, unique=True)
    hostname = Column(String(255), nullable=False)
    executor_kind = Column(String(64), nullable=False)
    role = Column(String(64), nullable=False, default="evaluator")
    slot_capacity = Column(Integer, nullable=False, default=1)
    capabilities = Column(json_type, nullable=False, default=dict)
    active = Column(Boolean, nullable=False, default=True)
    last_seen_at = Column(DateTime(timezone=True))

    leases = relationship("WorkerLease", back_populates="machine")
    runs = relationship("Run", back_populates="machine")

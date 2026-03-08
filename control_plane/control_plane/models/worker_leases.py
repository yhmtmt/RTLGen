"""Worker lease model."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, text
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, uuid_column
from control_plane.models.enums import LeaseStatus


class WorkerLease(Base):
    __tablename__ = "worker_leases"
    __table_args__ = (
        Index("ix_worker_leases_status_expires_at", "status", "expires_at"),
        Index("ix_worker_leases_machine_status", "machine_id", "status"),
        Index(
            "uq_worker_leases_active_work_item",
            "work_item_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id = uuid_column(primary_key=True)
    work_item_id = uuid_column(foreign_key=ForeignKey("work_items.id"), nullable=False)
    machine_id = uuid_column(foreign_key=ForeignKey("worker_machines.id"), nullable=False)
    lease_token = Column(String(255), nullable=False, unique=True)
    status = Column(Enum(LeaseStatus, native_enum=False), nullable=False, default=LeaseStatus.ACTIVE)
    leased_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at = Column(DateTime(timezone=True))

    work_item = relationship("WorkItem", back_populates="leases")
    machine = relationship("WorkerMachine", back_populates="leases")
    runs = relationship("Run", back_populates="lease")

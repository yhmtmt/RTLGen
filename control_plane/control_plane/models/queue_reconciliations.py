"""Queue import/export reconciliation model."""

from __future__ import annotations

from sqlalchemy import Column, Enum, ForeignKey, Index, String, Text

from control_plane.models.base import Base, TimestampMixin, uuid_column
from control_plane.models.enums import QueueReconciliationDirection, QueueReconciliationStatus


class QueueReconciliation(TimestampMixin, Base):
    __tablename__ = "queue_reconciliations"
    __table_args__ = (
        Index("ix_queue_reconciliations_item_created_at", "item_id", "created_at"),
        Index("ix_queue_reconciliations_direction_status_created_at", "direction", "status", "created_at"),
    )

    id = uuid_column(primary_key=True)
    item_id = Column(String(255), nullable=False)
    direction = Column(Enum(QueueReconciliationDirection, native_enum=False), nullable=False)
    queue_path = Column(Text, nullable=False)
    queue_sha256 = Column(String(64))
    db_work_item_id = uuid_column(foreign_key=ForeignKey("work_items.id"), nullable=True)
    status = Column(Enum(QueueReconciliationStatus, native_enum=False), nullable=False)
    message = Column(Text, nullable=False, default="")

"""Task request model."""

from __future__ import annotations

from sqlalchemy import Column, Enum, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, TimestampMixin, json_type, uuid_column
from control_plane.models.enums import FlowName, LayerName


class TaskRequest(TimestampMixin, Base):
    __tablename__ = "task_requests"
    __table_args__ = (
        Index("ix_task_requests_layer_flow_created_at", "layer", "flow", "created_at"),
    )

    id = uuid_column(primary_key=True)
    request_key = Column(String(255), nullable=False, unique=True)
    source = Column(String(64), nullable=False)
    requested_by = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    layer = Column(Enum(LayerName, native_enum=False), nullable=False)
    flow = Column(Enum(FlowName, native_enum=False), nullable=False)
    priority = Column(Integer, nullable=False, default=1)
    request_payload = Column(json_type, nullable=False, default=dict)
    source_commit = Column(String(64))

    work_items = relationship("WorkItem", back_populates="task_request")

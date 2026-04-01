"""Work item model."""

from __future__ import annotations

from sqlalchemy import Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, TimestampMixin, UpdatedAtMixin, json_type, uuid_column
from control_plane.models.enums import FlowName, LayerName, WorkItemState


class WorkItem(TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "work_items"
    __table_args__ = (
        Index("ix_work_items_state_priority_created_at", "state", "priority", "created_at"),
        Index("ix_work_items_layer_platform_state", "layer", "platform", "state"),
        Index("ix_work_items_assigned_machine_state", "assigned_machine_key", "state", "priority", "created_at"),
    )

    id = uuid_column(primary_key=True)
    work_item_key = Column(String(255), nullable=False, unique=True)
    task_request_id = uuid_column(foreign_key=ForeignKey("task_requests.id"), nullable=False)
    item_id = Column(String(255), nullable=False, unique=True)
    layer = Column(Enum(LayerName, native_enum=False), nullable=False)
    flow = Column(Enum(FlowName, native_enum=False), nullable=False)
    platform = Column(String(64), nullable=False)
    task_type = Column(String(64), nullable=False)
    state = Column(
        Enum(WorkItemState, native_enum=False, length=32),
        nullable=False,
        default=WorkItemState.DRAFT,
    )
    priority = Column(Integer, nullable=False)
    source_mode = Column(String(64))
    input_manifest = Column(json_type, nullable=False, default=dict)
    command_manifest = Column(json_type, nullable=False, default=list)
    expected_outputs = Column(json_type, nullable=False, default=list)
    acceptance_rules = Column(json_type, nullable=False, default=list)
    queue_snapshot_path = Column(Text)
    source_commit = Column(String(64))
    assigned_machine_key = Column(String(255))

    task_request = relationship("TaskRequest", back_populates="work_items")
    leases = relationship("WorkerLease", back_populates="work_item")
    runs = relationship("Run", back_populates="work_item")
    github_links = relationship("GitHubLink", back_populates="work_item")

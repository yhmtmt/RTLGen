"""Append-only run event model."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, json_type


class RunEvent(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        Index("ix_run_events_run_id_event_time", "run_id", "event_time"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    event_type = Column(String(128), nullable=False)
    event_payload = Column(json_type, nullable=False, default=dict)

    run = relationship("Run", back_populates="events")

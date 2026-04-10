"""Resolver observation model."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, String, Text

from control_plane.models.base import Base, TimestampMixin, json_type, uuid_column


class ResolverObservation(TimestampMixin, Base):
    __tablename__ = "resolver_observations"
    __table_args__ = (
        Index("ix_resolver_observations_case_created_at", "case_id", "created_at"),
        Index("ix_resolver_observations_source_kind_created_at", "source", "kind", "created_at"),
    )

    id = uuid_column(primary_key=True)
    case_id = uuid_column(foreign_key=ForeignKey("resolver_cases.id"), nullable=False)
    source = Column(String(32), nullable=False)
    kind = Column(String(64), nullable=False)
    summary = Column(Text, nullable=False, default="")
    payload_json = Column(json_type, nullable=False, default=dict)

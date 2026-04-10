"""Resolver action model."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, Integer, String, UniqueConstraint

from control_plane.models.base import Base, TimestampMixin, json_type, uuid_column


class ResolverAction(TimestampMixin, Base):
    __tablename__ = "resolver_actions"
    __table_args__ = (
        Index("ix_resolver_actions_case_created_at", "case_id", "created_at"),
        Index("ix_resolver_actions_action_status_created_at", "action_key", "status", "created_at"),
        UniqueConstraint("idempotency_key", name="uq_resolver_actions_idempotency_key"),
    )

    id = uuid_column(primary_key=True)
    case_id = uuid_column(foreign_key=ForeignKey("resolver_cases.id"), nullable=False)
    actor = Column(String(32), nullable=False)
    action_type = Column(String(64), nullable=False)
    action_key = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    attempt_index = Column(Integer, nullable=False)
    evidence_hash = Column(String(64))
    failure_hash = Column(String(64))
    idempotency_key = Column(String(255), nullable=False)
    request_json = Column(json_type, nullable=False, default=dict)
    result_json = Column(json_type, nullable=False, default=dict)

"""Resolver case model."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from control_plane.models.base import Base, TimestampMixin, UpdatedAtMixin, json_type, uuid_column


class ResolverCase(TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "resolver_cases"
    __table_args__ = (
        Index("ix_resolver_cases_status_created_at", "status", "created_at"),
        Index("ix_resolver_cases_owner_status_created_at", "owner", "status", "created_at"),
        Index("ix_resolver_cases_fingerprint_status", "fingerprint", "status"),
    )

    id = uuid_column(primary_key=True)
    fingerprint = Column(String(255), nullable=False)
    failure_class = Column(String(128), nullable=False)
    owner = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    severity = Column(String(32), nullable=False, default="medium")

    issue_number = Column(Integer)
    first_item_id = Column(String(255))
    latest_item_id = Column(String(255))
    first_run_key = Column(String(255))
    latest_run_key = Column(String(255))
    machine_key = Column(String(255))
    source_commit = Column(String(64))
    repo_root = Column(Text)

    evidence_json = Column(json_type, nullable=False, default=dict)
    resolution_json = Column(json_type, nullable=False, default=dict)

    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)

    last_evidence_hash = Column(String(64))
    last_attempted_evidence_hash = Column(String(64))
    last_failure_hash = Column(String(64))
    last_action_type = Column(String(64))
    last_action_status = Column(String(32))

    escalation_reason = Column(Text)
    resolved_at = Column(DateTime(timezone=True))
    escalated_at = Column(DateTime(timezone=True))

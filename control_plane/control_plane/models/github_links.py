"""GitHub branch and PR linkage model."""

from __future__ import annotations

from sqlalchemy import Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, TimestampMixin, UpdatedAtMixin, json_type, uuid_column
from control_plane.models.enums import GitHubLinkState


class GitHubLink(TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "github_links"
    __table_args__ = (
        Index("ix_github_links_pr_number", "pr_number"),
        Index("ix_github_links_branch_name", "branch_name"),
        Index("ix_github_links_work_item_state", "work_item_id", "state"),
    )

    id = uuid_column(primary_key=True)
    work_item_id = uuid_column(foreign_key=ForeignKey("work_items.id"), nullable=False)
    run_id = uuid_column(foreign_key=ForeignKey("runs.id"), nullable=True)
    repo = Column(String(255), nullable=False)
    branch_name = Column(String(255))
    pr_number = Column(Integer)
    pr_url = Column(Text)
    head_sha = Column(String(64))
    base_branch = Column(String(255))
    state = Column(Enum(GitHubLinkState, native_enum=False), nullable=False, default=GitHubLinkState.NONE)
    metadata_ = Column("metadata", json_type, nullable=False, default=dict)

    work_item = relationship("WorkItem", back_populates="github_links")
    run = relationship("Run", back_populates="github_links")

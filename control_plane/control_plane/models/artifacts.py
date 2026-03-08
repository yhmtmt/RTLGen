"""Artifact model."""

from __future__ import annotations

from sqlalchemy import Column, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from control_plane.models.base import Base, TimestampMixin, json_type, uuid_column
from control_plane.models.enums import ArtifactStorageMode


class Artifact(TimestampMixin, Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        Index("ix_artifacts_run_id_kind", "run_id", "kind"),
        Index("ix_artifacts_storage_mode_kind", "storage_mode", "kind"),
    )

    id = uuid_column(primary_key=True)
    run_id = uuid_column(foreign_key=ForeignKey("runs.id"), nullable=False)
    kind = Column(String(64), nullable=False)
    storage_mode = Column(Enum(ArtifactStorageMode, native_enum=False), nullable=False)
    path = Column(Text, nullable=False)
    sha256 = Column(String(64))
    metadata_ = Column("metadata", json_type, nullable=False, default=dict)

    run = relationship("Run", back_populates="artifacts")

"""Shared SQLAlchemy base, naming conventions, and column helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, JSON, MetaData, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)
json_type = JSON().with_variant(JSONB(astext_type=String()), "postgresql")


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UpdatedAtMixin:
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


def make_uuid() -> str:
    return str(uuid.uuid4())


def uuid_column(primary_key: bool = False, nullable: bool = False, foreign_key=None):
    args = []
    if foreign_key is not None:
        args.append(foreign_key)
    kwargs = {
        "primary_key": primary_key,
        "nullable": nullable,
    }
    if primary_key:
        kwargs["default"] = make_uuid
    return Column(String(36), *args, **kwargs)

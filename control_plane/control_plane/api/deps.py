"""Shared dependency helpers for API handlers."""

from __future__ import annotations

from control_plane.config import Settings


def get_settings() -> Settings:
    return Settings.from_env()

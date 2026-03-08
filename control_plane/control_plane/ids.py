"""Identifier helpers for queue items, leases, and runs."""

from __future__ import annotations

import secrets


def make_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"

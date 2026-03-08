"""Smoke coverage for the cp-002 relational model."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect

from control_plane.db import create_all


EXPECTED_TABLES = {
    "artifacts",
    "github_links",
    "queue_reconciliations",
    "run_events",
    "runs",
    "task_requests",
    "work_items",
    "worker_leases",
    "worker_machines",
}


def test_create_all_sqlite() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert EXPECTED_TABLES.issubset(tables)

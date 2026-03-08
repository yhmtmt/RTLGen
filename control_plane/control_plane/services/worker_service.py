"""Worker-loop orchestration helpers for cp-008."""

from __future__ import annotations

from dataclasses import asdict

from sqlalchemy.orm import sessionmaker

from control_plane.workers.executor import WorkerConfig, WorkerLoopResult, execute_worker_loop


def run_worker(session_factory: sessionmaker, *, config: WorkerConfig, max_items: int = 1) -> list[WorkerLoopResult]:
    return execute_worker_loop(session_factory, config=config, max_items=max_items)


def render_worker_results(results: list[WorkerLoopResult]) -> list[dict[str, object]]:
    return [asdict(result) for result in results]

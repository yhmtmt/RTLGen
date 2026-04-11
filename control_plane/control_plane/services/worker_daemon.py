"""Polling supervisor for the internal worker loop."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time
from typing import Callable

from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import sessionmaker

from control_plane.clock import utcnow
from control_plane.services.lease_service import expire_stale_leases
from control_plane.services.worker_service import run_worker
from control_plane.workers.executor import WorkerConfig, WorkerLoopResult


@dataclass(frozen=True)
class WorkerDaemonConfig:
    worker: WorkerConfig
    poll_seconds: int = 15
    max_items_per_poll: int = 1
    concurrency: int = 1
    max_polls: int | None = None
    stop_on_no_work: bool = False
    run_scheduler_maintenance: bool = True


@dataclass(frozen=True)
class WorkerDaemonResult:
    poll_count: int
    executed_items: int
    no_work_polls: int
    results: list[WorkerLoopResult]


def _default_log(message: str) -> None:
    print(f"[{utcnow().isoformat().replace('+00:00', 'Z')}] {message}", flush=True)


def _dispose_session_engine(session_factory: sessionmaker, logger: Callable[[str], None]) -> None:
    engine = getattr(session_factory, "kw", {}).get("bind")
    if engine is None:
        return
    try:
        engine.dispose()
    except Exception as exc:  # pragma: no cover - defensive cleanup
        logger(f"worker-daemon engine_dispose_error error={exc}")


def _is_retryable_db_error(exc: Exception) -> bool:
    return isinstance(exc, (OperationalError, DBAPIError))


def _run_parallel_batch(
    session_factory: sessionmaker,
    *,
    config: WorkerDaemonConfig,
) -> list[WorkerLoopResult]:
    target = max(1, config.max_items_per_poll)
    slots = max(1, min(config.concurrency, target))
    if slots == 1:
        return run_worker(session_factory, config=config.worker, max_items=target)

    results: list[WorkerLoopResult] = []
    remaining = target
    while remaining > 0:
        batch_size = min(slots, remaining)
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [
                executor.submit(run_worker, session_factory, config=config.worker, max_items=1)
                for _ in range(batch_size)
            ]
            batch: list[WorkerLoopResult] = []
            for future in futures:
                batch.extend(future.result())
        results.extend(batch)
        remaining -= len(batch)
        if any(result.status == "no_work" for result in batch):
            break
    return results


def run_worker_daemon(
    session_factory: sessionmaker,
    *,
    config: WorkerDaemonConfig,
    log_fn: Callable[[str], None] | None = None,
) -> WorkerDaemonResult:
    logger = log_fn or _default_log
    poll_count = 0
    executed_items = 0
    no_work_polls = 0
    results: list[WorkerLoopResult] = []

    logger(
        "worker-daemon start "
        f"machine_key={config.worker.machine_key} "
        f"hostname={config.worker.hostname} "
        f"poll_seconds={config.poll_seconds} "
        f"max_items_per_poll={config.max_items_per_poll} "
        f"concurrency={config.concurrency}"
    )

    while config.max_polls is None or poll_count < config.max_polls:
        poll_count += 1
        if config.run_scheduler_maintenance:
            try:
                with session_factory() as session:
                    expire_stale_leases(session)
            except Exception as exc:
                if _is_retryable_db_error(exc):
                    logger(f"worker-daemon db_unavailable stage=maintenance error={exc}")
                    _dispose_session_engine(session_factory, logger)
                    if config.max_polls is not None and poll_count >= config.max_polls:
                        logger("worker-daemon stop reason=max_polls")
                        break
                    time.sleep(config.poll_seconds)
                    continue
                raise

        try:
            batch = _run_parallel_batch(session_factory, config=config)
        except Exception as exc:
            if _is_retryable_db_error(exc):
                logger(f"worker-daemon db_unavailable stage=batch error={exc}")
                _dispose_session_engine(session_factory, logger)
                if config.max_polls is not None and poll_count >= config.max_polls:
                    logger("worker-daemon stop reason=max_polls")
                    break
                time.sleep(config.poll_seconds)
                continue
            logger(f"worker-daemon batch_error error={exc}")
            batch = [WorkerLoopResult(status="worker_error", summary=str(exc))]

        results.extend(batch)

        batch_executed = sum(1 for result in batch if result.status != "no_work")
        executed_items += batch_executed
        logger(
            "worker-daemon poll "
            f"poll={poll_count} "
            f"executed={batch_executed} "
            f"results={[{'item_id': row.item_id, 'status': row.status} for row in batch]}"
        )
        batch_no_work = all(result.status == "no_work" for result in batch)
        if batch_no_work:
            no_work_polls += 1
            if config.stop_on_no_work:
                logger("worker-daemon stop reason=no_work")
                break
            time.sleep(config.poll_seconds)
            continue

        if config.max_polls is not None and poll_count >= config.max_polls:
            logger("worker-daemon stop reason=max_polls")
            break
        time.sleep(config.poll_seconds)

    logger(
        "worker-daemon exit "
        f"poll_count={poll_count} "
        f"executed_items={executed_items} "
        f"no_work_polls={no_work_polls}"
    )
    return WorkerDaemonResult(
        poll_count=poll_count,
        executed_items=executed_items,
        no_work_polls=no_work_polls,
        results=results,
    )

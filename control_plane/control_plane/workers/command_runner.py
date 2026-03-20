"""Command execution helpers for the internal worker loop."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import shlex
import subprocess
import time
from typing import Any, Callable


CommandCallback = Callable[["CommandResult"], None]
CommandStartCallback = Callable[[dict[str, Any]], None]
CommandProgressCallback = Callable[[dict[str, Any]], None]
CancelCheck = Callable[[], bool]


class CommandExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    name: str
    command: str
    returncode: int
    duration_seconds: float
    stdout_log: str
    stderr_log: str
    timed_out: bool
    stalled: bool
    canceled: bool


def _command_filename(index: int, name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name).strip("_")
    return f"{index:02d}_{safe or 'command'}"


def run_command_manifest(
    *,
    command_manifest: list[dict[str, Any]],
    work_dir: str,
    log_dir: str,
    timeout_seconds: int | None = None,
    stall_timeout_seconds: int | None = None,
    progress_interval_seconds: int = 60,
    env: dict[str, str] | None = None,
    cancel_requested: CancelCheck | None = None,
    on_command_started: CommandStartCallback | None = None,
    on_command_progress: CommandProgressCallback | None = None,
    on_command_finished: CommandCallback | None = None,
) -> list[CommandResult]:
    log_root = Path(log_dir)
    log_root.mkdir(parents=True, exist_ok=True)
    results: list[CommandResult] = []
    for index, command_spec in enumerate(command_manifest, start=1):
        name = str(command_spec.get("name") or f"command_{index}")
        command = command_spec.get("run")
        if not command:
            raise CommandExecutionError(f"command manifest entry missing run field: index={index}")

        stem = _command_filename(index, name)
        stdout_path = log_root / f"{stem}.stdout.log"
        stderr_path = log_root / f"{stem}.stderr.log"

        started = time.monotonic()
        timed_out = False
        stalled = False
        canceled = False
        if on_command_started is not None:
            on_command_started(
                {
                    "command_name": name,
                    "command": command,
                    "stdout_log": str(stdout_path),
                    "stderr_log": str(stderr_path),
                }
            )

        with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            process = subprocess.Popen(
                ["bash", "-lc", command],
                cwd=work_dir,
                env=env,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                start_new_session=True,
            )
            returncode = _monitor_command(
                command_name=name,
                process=process,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                timeout_seconds=timeout_seconds,
                stall_timeout_seconds=stall_timeout_seconds,
                progress_interval_seconds=progress_interval_seconds,
                cancel_requested=cancel_requested,
                on_command_progress=on_command_progress,
            )
            timed_out = returncode == 124
            stalled = returncode == 125
            canceled = returncode == 130
        duration_seconds = time.monotonic() - started

        result = CommandResult(
            name=name,
            command=command,
            returncode=returncode,
            duration_seconds=duration_seconds,
            stdout_log=str(stdout_path),
            stderr_log=str(stderr_path),
            timed_out=timed_out,
            stalled=stalled,
            canceled=canceled,
        )
        results.append(result)
        if on_command_finished is not None:
            on_command_finished(result)
        if returncode != 0:
            break
    return results


def summarize_command_results(results: list[CommandResult]) -> str:
    if not results:
        return "no commands executed"
    failed = next((result for result in results if result.returncode != 0), None)
    if failed is not None:
        if failed.canceled:
            detail = "canceled"
        elif failed.stalled:
            detail = "stalled"
        elif failed.timed_out:
            detail = "timed out"
        else:
            detail = f"exit_code={failed.returncode}"
        return f"command {failed.name} failed ({detail})"
    return f"{len(results)}/{len(results)} commands succeeded"


def shell_preview(command: str) -> list[str]:
    return shlex.split(command)


def _terminate_process_group(process: subprocess.Popen[str], *, force: bool = False) -> None:
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        return


def _last_output_age_seconds(*, stdout_path: Path, stderr_path: Path) -> float:
    timestamps = []
    for path in (stdout_path, stderr_path):
        if path.exists():
            timestamps.append(path.stat().st_mtime)
    if not timestamps:
        return 0.0
    return max(0.0, time.time() - max(timestamps))


def _monitor_command(
    *,
    command_name: str,
    process: subprocess.Popen[str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int | None,
    stall_timeout_seconds: int | None,
    progress_interval_seconds: int,
    cancel_requested: CancelCheck | None,
    on_command_progress: CommandProgressCallback | None,
) -> int:
    started = time.monotonic()
    next_progress = started + max(1, progress_interval_seconds)
    while True:
        now = time.monotonic()
        returncode = process.poll()
        if returncode is not None:
            return returncode

        if cancel_requested is not None and cancel_requested():
            _terminate_process_group(process)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _terminate_process_group(process, force=True)
                process.wait(timeout=5)
            return 130

        if timeout_seconds is not None and now - started >= timeout_seconds:
            _terminate_process_group(process)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _terminate_process_group(process, force=True)
                process.wait(timeout=5)
            return 124

        last_output_age = _last_output_age_seconds(stdout_path=stdout_path, stderr_path=stderr_path)
        if stall_timeout_seconds is not None and last_output_age >= stall_timeout_seconds:
            _terminate_process_group(process)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _terminate_process_group(process, force=True)
                process.wait(timeout=5)
            return 125

        if on_command_progress is not None and now >= next_progress:
            on_command_progress(
                {
                    "command_name": command_name,
                    "elapsed_seconds": now - started,
                    "stdout_log": str(stdout_path),
                    "stderr_log": str(stderr_path),
                    "stdout_bytes": stdout_path.stat().st_size if stdout_path.exists() else 0,
                    "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
                    "last_output_age_seconds": last_output_age,
                }
            )
            next_progress = now + max(1, progress_interval_seconds)

        time.sleep(1)

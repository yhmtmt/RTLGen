"""Command execution helpers for the internal worker loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess
import time
from typing import Any, Callable


CommandCallback = Callable[["CommandResult"], None]


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


def _command_filename(index: int, name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in name).strip("_")
    return f"{index:02d}_{safe or 'command'}"


def run_command_manifest(
    *,
    command_manifest: list[dict[str, Any]],
    work_dir: str,
    log_dir: str,
    timeout_seconds: int | None = None,
    env: dict[str, str] | None = None,
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
        try:
            completed = subprocess.run(
                ["bash", "-lc", command],
                cwd=work_dir,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            returncode = completed.returncode
            stdout_text = completed.stdout
            stderr_text = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = 124
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or ""
        duration_seconds = time.monotonic() - started

        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")

        result = CommandResult(
            name=name,
            command=command,
            returncode=returncode,
            duration_seconds=duration_seconds,
            stdout_log=str(stdout_path),
            stderr_log=str(stderr_path),
            timed_out=timed_out,
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
        detail = "timed out" if failed.timed_out else f"exit_code={failed.returncode}"
        return f"command {failed.name} failed ({detail})"
    return f"{len(results)}/{len(results)} commands succeeded"


def shell_preview(command: str) -> list[str]:
    return shlex.split(command)

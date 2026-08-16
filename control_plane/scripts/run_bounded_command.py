#!/usr/bin/env python3
"""Run a command under bounded resources with a systemd or portable backend."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import errno
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from typing import Any, Sequence

TIMEOUT_EXIT_CODE = 124
TASKS_MAX_EXIT_CODE = 125
_SYSTEMD_CHECK_TIMEOUT_SEC = 5.0
_TERM_GRACE_SEC = 5.0
_POLL_INTERVAL_SEC = 0.05
_SIZE_SUFFIXES = {
    "": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
}
_PR_SET_CHILD_SUBREAPER = 36
_PR_GET_CHILD_SUBREAPER = 37
_LIBC = ctypes.CDLL(None, use_errno=True) if sys.platform.startswith("linux") else None


@dataclass(frozen=True)
class LimitSpec:
    memory_high: str | None
    memory_max: str | None
    cpu_quota: str | None
    tasks_max: int | None
    runtime_max_sec: int | None


@dataclass(frozen=True)
class SystemdProbeResult:
    usable: bool
    reason: str


@dataclass(frozen=True)
class _ProcInfo:
    pid: int
    ppid: int
    pgid: int
    sid: int


class _TerminationSignalState:
    def __init__(self) -> None:
        self.requested_signal: int | None = None
        self._previous_handlers: dict[int, Any] = {}

    def install(self, *signals_to_handle: int) -> None:
        for signal_number in signals_to_handle:
            self._previous_handlers[signal_number] = signal.getsignal(signal_number)
            signal.signal(signal_number, self._handle_signal)

    def restore(self) -> None:
        for signal_number, previous in self._previous_handlers.items():
            signal.signal(signal_number, previous)
        self._previous_handlers.clear()

    def _handle_signal(self, signal_number: int, _frame: Any) -> None:
        self.requested_signal = signal_number


def _parse_size(text: str) -> int:
    value = str(text).strip()
    if not value:
        raise argparse.ArgumentTypeError("size must not be empty")
    upper = value.upper()
    if upper.endswith("IB"):
        upper = upper[:-2]
    elif upper.endswith("B") and len(upper) > 1:
        upper = upper[:-1]
    suffix = upper[-1] if upper and upper[-1].isalpha() else ""
    digits = upper[:-1] if suffix else upper
    if suffix not in _SIZE_SUFFIXES or not digits.isdigit():
        raise argparse.ArgumentTypeError(f"invalid size value: {text}")
    number = int(digits)
    if number <= 0:
        raise argparse.ArgumentTypeError(f"size must be positive: {text}")
    return number * _SIZE_SUFFIXES[suffix]


def _parse_positive_size_arg(text: str) -> str:
    _parse_size(text)
    return text


def _parse_cpu_quota_percent(text: str) -> float:
    value = str(text).strip()
    if not value.endswith("%"):
        raise argparse.ArgumentTypeError(f"cpu quota must end with %: {text}")
    try:
        percent = float(value[:-1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid cpu quota: {text}") from exc
    if percent <= 0:
        raise argparse.ArgumentTypeError(f"cpu quota must be positive: {text}")
    return percent


def _parse_cpu_quota_arg(text: str) -> str:
    _parse_cpu_quota_percent(text)
    return text


def _parse_tasks_max(text: str) -> int:
    try:
        value = int(str(text).strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid tasks-max: {text}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError(f"tasks-max must be positive: {text}")
    return value


def _parse_runtime_max_sec(text: str) -> int:
    try:
        value = int(str(text).strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid runtime-max-sec: {text}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError(f"runtime-max-sec must be positive: {text}")
    return value


def parse_cli(argv: Sequence[str]) -> tuple[LimitSpec, list[str]]:
    raw_args = list(argv)
    if "--" not in raw_args:
        raise SystemExit("missing `--` separator before child command")
    split_index = raw_args.index("--")
    child_command = raw_args[split_index + 1 :]
    if not child_command:
        raise SystemExit("missing child command after `--`")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-high", type=_parse_positive_size_arg, default=None)
    parser.add_argument("--memory-max", type=_parse_positive_size_arg, default=None)
    parser.add_argument("--cpu-quota", type=_parse_cpu_quota_arg, default=None)
    parser.add_argument("--tasks-max", type=_parse_tasks_max, default=None)
    parser.add_argument("--runtime-max-sec", type=_parse_runtime_max_sec, default=None)
    namespace = parser.parse_args(raw_args[:split_index])
    spec = LimitSpec(
        memory_high=namespace.memory_high,
        memory_max=namespace.memory_max,
        cpu_quota=namespace.cpu_quota,
        tasks_max=namespace.tasks_max,
        runtime_max_sec=namespace.runtime_max_sec,
    )
    return spec, child_command


def _normalize_exit_code(returncode: int) -> int:
    if returncode < 0:
        return 128 + abs(returncode)
    return returncode


def _selected_cpu_count(cpu_quota: str | None) -> int | None:
    if cpu_quota is None:
        return None
    percent = _parse_cpu_quota_percent(cpu_quota)
    return max(1, math.ceil(percent / 100.0))


def _select_affinity(allowed_cpus: Sequence[int], cpu_quota: str | None) -> tuple[int, ...]:
    normalized = tuple(sorted(int(cpu) for cpu in allowed_cpus))
    if not normalized:
        return ()
    selected_count = _selected_cpu_count(cpu_quota)
    if selected_count is None:
        return normalized
    return normalized[: min(len(normalized), selected_count)]


def _detect_systemd_user_manager(
    *,
    env: dict[str, str] | None = None,
    which: Any = shutil.which,
    run: Any = subprocess.run,
) -> SystemdProbeResult:
    effective_env = dict(os.environ if env is None else env)
    systemd_run_path = which("systemd-run")
    if systemd_run_path is None:
        return SystemdProbeResult(usable=False, reason="systemd_tools_missing")
    missing = [name for name in ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR") if not effective_env.get(name)]
    if missing:
        return SystemdProbeResult(usable=False, reason=f"missing_env:{','.join(missing)}")
    runtime_dir = effective_env["XDG_RUNTIME_DIR"]
    if not Path(runtime_dir).is_dir():
        return SystemdProbeResult(usable=False, reason="xdg_runtime_dir_missing")
    true_path = which("true") or "/bin/true"
    try:
        result = run(
            [systemd_run_path, "--user", "--scope", "--quiet", true_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=_SYSTEMD_CHECK_TIMEOUT_SEC,
            env=effective_env,
        )
    except OSError as exc:
        return SystemdProbeResult(usable=False, reason=f"systemd_run_exec_error:{exc.errno or 'unknown'}")
    except subprocess.TimeoutExpired:
        return SystemdProbeResult(usable=False, reason="systemd_run_scope_timeout")
    if result.returncode != 0:
        return SystemdProbeResult(usable=False, reason=f"systemd_run_scope_exit:{result.returncode}")
    return SystemdProbeResult(usable=True, reason="systemd_run_scope_ok")


def _build_systemd_command(spec: LimitSpec, child_command: Sequence[str]) -> list[str]:
    command = ["systemd-run", "--user", "--scope"]
    if spec.memory_high is not None:
        command.extend(["-p", f"MemoryHigh={spec.memory_high}"])
    if spec.memory_max is not None:
        command.extend(["-p", f"MemoryMax={spec.memory_max}"])
    if spec.cpu_quota is not None:
        command.extend(["-p", f"CPUQuota={spec.cpu_quota}"])
    if spec.tasks_max is not None:
        command.extend(["-p", f"TasksMax={spec.tasks_max}"])
    if spec.runtime_max_sec is not None:
        command.extend(["-p", f"RuntimeMaxSec={spec.runtime_max_sec}"])
    command.extend(child_command)
    return command


def _apply_fallback_limits(
    spec: LimitSpec,
    *,
    allowed_cpus: Sequence[int],
    setrlimit: Any = resource.setrlimit,
    sched_setaffinity: Any | None = getattr(os, "sched_setaffinity", None),
) -> tuple[int, ...]:
    selected_cpus = _select_affinity(allowed_cpus, spec.cpu_quota)
    if spec.memory_max is not None:
        memory_limit = _parse_size(spec.memory_max)
        setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    if sched_setaffinity is not None and selected_cpus:
        sched_setaffinity(0, selected_cpus)
    return selected_cpus


def _portable_backend_diagnostic(
    spec: LimitSpec,
    *,
    probe: SystemdProbeResult,
    allowed_cpus: Sequence[int],
) -> dict[str, Any]:
    selected_cpus = list(_select_affinity(allowed_cpus, spec.cpu_quota))
    return {
        "event": "run_bounded_command",
        "backend": "portable_fallback",
        "systemd_probe": {"usable": probe.usable, "reason": probe.reason},
        "limits": {
            "memory_high": spec.memory_high,
            "memory_max": spec.memory_max,
            "cpu_quota": spec.cpu_quota,
            "tasks_max": spec.tasks_max,
            "runtime_max_sec": spec.runtime_max_sec,
        },
        "enforcement": {
            "memory_high": "advisory_unavailable",
            "memory_max": "rlimit_as" if spec.memory_max is not None else None,
            "cpu_quota": "sched_affinity_ceiling" if spec.cpu_quota is not None else None,
            "tasks_max": "process_tree_task_monitor" if spec.tasks_max is not None else None,
            "runtime_max_sec": "process_group_timeout" if spec.runtime_max_sec is not None else None,
        },
        "allowed_cpus": list(sorted(int(cpu) for cpu in allowed_cpus)),
        "selected_cpus": selected_cpus,
    }


def _systemd_backend_diagnostic(spec: LimitSpec, *, probe: SystemdProbeResult) -> dict[str, Any]:
    return {
        "event": "run_bounded_command",
        "backend": "systemd_user_scope",
        "systemd_probe": {"usable": probe.usable, "reason": probe.reason},
        "limits": {
            "memory_high": spec.memory_high,
            "memory_max": spec.memory_max,
            "cpu_quota": spec.cpu_quota,
            "tasks_max": spec.tasks_max,
            "runtime_max_sec": spec.runtime_max_sec,
        },
        "enforcement": {
            "memory_high": "cgroup_memoryhigh" if spec.memory_high is not None else None,
            "memory_max": "cgroup_memorymax" if spec.memory_max is not None else None,
            "cpu_quota": "cgroup_cpuquota" if spec.cpu_quota is not None else None,
            "tasks_max": "cgroup_tasksmax" if spec.tasks_max is not None else None,
            "runtime_max_sec": "systemd_runtimemaxsec" if spec.runtime_max_sec is not None else None,
        },
    }


def _emit_diagnostic(payload: dict[str, Any], *, stream: Any = sys.stderr) -> None:
    stream.write(json.dumps(payload, sort_keys=True))
    stream.write("\n")
    stream.flush()


def _shell_error_code(exc: OSError) -> int:
    if exc.errno == errno.ENOENT:
        return 127
    return 126


def _set_child_subreaper(enabled: bool) -> bool | None:
    if _LIBC is None:
        return None
    current = ctypes.c_int()
    if _LIBC.prctl(_PR_GET_CHILD_SUBREAPER, ctypes.byref(current), 0, 0, 0) != 0:
        return None
    previous = bool(current.value)
    if _LIBC.prctl(_PR_SET_CHILD_SUBREAPER, int(enabled), 0, 0, 0) != 0:
        return None
    return previous


def _restore_child_subreaper(previous: bool | None) -> None:
    if previous is None or _LIBC is None:
        return
    _LIBC.prctl(_PR_SET_CHILD_SUBREAPER, int(previous), 0, 0, 0)


def _snapshot_process_table() -> dict[int, _ProcInfo]:
    snapshot: dict[int, _ProcInfo] = {}
    try:
        proc_entries = Path("/proc").iterdir()
    except OSError:
        return snapshot
    for proc_dir in proc_entries:
        if not proc_dir.name.isdigit():
            continue
        try:
            stat_text = (proc_dir / "stat").read_text(encoding="utf-8")
            comm_end = stat_text.rfind(")")
            if comm_end < 0:
                continue
            fields = stat_text[comm_end + 2 :].split()
            if len(fields) < 4:
                continue
            pid = int(proc_dir.name)
            snapshot[pid] = _ProcInfo(
                pid=pid,
                ppid=int(fields[1]),
                pgid=int(fields[2]),
                sid=int(fields[3]),
            )
        except (FileNotFoundError, OSError, ValueError):
            continue
    return snapshot


def _collect_descendant_processes(owner_pid: int) -> dict[int, _ProcInfo]:
    snapshot = _snapshot_process_table()
    children_by_parent: dict[int, list[_ProcInfo]] = {}
    for proc in snapshot.values():
        children_by_parent.setdefault(proc.ppid, []).append(proc)
    descendants: dict[int, _ProcInfo] = {}
    pending = [owner_pid]
    while pending:
        parent_pid = pending.pop()
        for child in children_by_parent.get(parent_pid, []):
            if child.pid in descendants:
                continue
            descendants[child.pid] = child
            pending.append(child.pid)
    return descendants


def _count_descendant_tasks(owner_pid: int) -> int:
    task_count = 0
    for proc in _collect_descendant_processes(owner_pid).values():
        try:
            task_count += sum(1 for entry in Path(f"/proc/{proc.pid}/task").iterdir() if entry.name.isdigit())
        except (FileNotFoundError, OSError):
            continue
    return task_count


def _reap_descendant_processes(owner_pid: int, *, excluded_pid: int) -> None:
    for proc in _collect_descendant_processes(owner_pid).values():
        if proc.pid == excluded_pid:
            continue
        try:
            os.waitpid(proc.pid, os.WNOHANG)
        except (ChildProcessError, ProcessLookupError):
            continue


def _signal_descendant_tree(owner_pid: int, signal_number: int) -> None:
    descendants = _collect_descendant_processes(owner_pid)
    process_groups = sorted({proc.pgid for proc in descendants.values() if proc.pgid > 0})
    for process_group in process_groups:
        try:
            os.killpg(process_group, signal_number)
        except ProcessLookupError:
            continue
    for proc in descendants.values():
        try:
            os.kill(proc.pid, signal_number)
        except ProcessLookupError:
            continue


def _wait_for_descendant_exit(owner_pid: int, process: subprocess.Popen[Any], deadline: float) -> bool:
    while time.monotonic() < deadline:
        _reap_descendant_processes(owner_pid, excluded_pid=process.pid)
        if process.poll() is not None and not _collect_descendant_processes(owner_pid):
            return True
        time.sleep(_POLL_INTERVAL_SEC)
    _reap_descendant_processes(owner_pid, excluded_pid=process.pid)
    return process.poll() is not None and not _collect_descendant_processes(owner_pid)


def _terminate_process_tree(process: subprocess.Popen[Any], *, term_grace_sec: float) -> None:
    owner_pid = os.getpid()
    _signal_descendant_tree(owner_pid, signal.SIGTERM)
    if _wait_for_descendant_exit(owner_pid, process, time.monotonic() + term_grace_sec):
        return
    _signal_descendant_tree(owner_pid, signal.SIGKILL)
    _wait_for_descendant_exit(owner_pid, process, time.monotonic() + term_grace_sec)


def _run_systemd_command(spec: LimitSpec, child_command: Sequence[str]) -> int:
    try:
        result = subprocess.run(_build_systemd_command(spec, child_command), check=False)
    except OSError as exc:
        return _shell_error_code(exc)
    return _normalize_exit_code(result.returncode)


def _run_portable_fallback(
    spec: LimitSpec,
    child_command: Sequence[str],
    *,
    term_grace_sec: float = _TERM_GRACE_SEC,
) -> int:
    if hasattr(os, "sched_getaffinity"):
        allowed_cpus = tuple(sorted(int(cpu) for cpu in os.sched_getaffinity(0)))
    else:
        cpu_total = os.cpu_count() or 1
        allowed_cpus = tuple(range(cpu_total))

    def preexec() -> None:
        os.setsid()
        _apply_fallback_limits(spec, allowed_cpus=allowed_cpus)

    previous_subreaper = _set_child_subreaper(True)
    signal_state = _TerminationSignalState()
    signal_state.install(signal.SIGTERM, signal.SIGINT)
    try:
        process = subprocess.Popen(child_command, preexec_fn=preexec)
    except OSError as exc:
        signal_state.restore()
        _restore_child_subreaper(previous_subreaper)
        return _shell_error_code(exc)
    try:
        started = time.monotonic()
        while True:
            returncode = process.poll()
            if returncode is not None:
                return _normalize_exit_code(returncode)
            if signal_state.requested_signal is not None:
                _terminate_process_tree(process, term_grace_sec=term_grace_sec)
                process.wait()
                return 128 + signal_state.requested_signal
            if spec.tasks_max is not None:
                observed_tasks = _count_descendant_tasks(os.getpid())
                if observed_tasks > spec.tasks_max:
                    _emit_diagnostic(
                        {
                            "event": "run_bounded_command_tasks_max_exceeded",
                            "backend": "portable_fallback",
                            "tasks_max": spec.tasks_max,
                            "observed_tasks": observed_tasks,
                            "term_grace_sec": term_grace_sec,
                        }
                    )
                    _terminate_process_tree(process, term_grace_sec=term_grace_sec)
                    process.wait()
                    return TASKS_MAX_EXIT_CODE
            if spec.runtime_max_sec is not None and time.monotonic() - started >= spec.runtime_max_sec:
                _emit_diagnostic(
                    {
                        "event": "run_bounded_command_timeout",
                        "backend": "portable_fallback",
                        "runtime_max_sec": spec.runtime_max_sec,
                        "term_grace_sec": term_grace_sec,
                    }
                )
                _terminate_process_tree(process, term_grace_sec=term_grace_sec)
                process.wait()
                return TIMEOUT_EXIT_CODE
            time.sleep(_POLL_INTERVAL_SEC)
    finally:
        _reap_descendant_processes(os.getpid(), excluded_pid=process.pid)
        signal_state.restore()
        _restore_child_subreaper(previous_subreaper)


def main(argv: Sequence[str] | None = None) -> int:
    spec, child_command = parse_cli(list(sys.argv[1:] if argv is None else argv))
    probe = _detect_systemd_user_manager()
    if probe.usable:
        _emit_diagnostic(_systemd_backend_diagnostic(spec, probe=probe))
        return _run_systemd_command(spec, child_command)
    if hasattr(os, "sched_getaffinity"):
        allowed_cpus = tuple(sorted(int(cpu) for cpu in os.sched_getaffinity(0)))
    else:
        cpu_total = os.cpu_count() or 1
        allowed_cpus = tuple(range(cpu_total))
    _emit_diagnostic(_portable_backend_diagnostic(spec, probe=probe, allowed_cpus=allowed_cpus))
    return _run_portable_fallback(spec, child_command)


if __name__ == "__main__":
    sys.exit(main())

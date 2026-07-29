#!/usr/bin/env python3
"""Run a command under bounded resources with a systemd or portable backend."""

from __future__ import annotations

import argparse
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
_SYSTEMD_CHECK_TIMEOUT_SEC = 5.0
_TERM_GRACE_SEC = 5.0
_SIZE_SUFFIXES = {
    "": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
}


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
    if spec.tasks_max is not None:
        setrlimit(resource.RLIMIT_NPROC, (spec.tasks_max, spec.tasks_max))
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
            "tasks_max": "rlimit_nproc" if spec.tasks_max is not None else None,
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


def _terminate_process_group(process: subprocess.Popen[Any], *, term_grace_sec: float) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + term_grace_sec
    while time.monotonic() < deadline:
        if process.poll() is not None:
            return
        time.sleep(0.05)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return


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

    try:
        process = subprocess.Popen(child_command, preexec_fn=preexec)
    except OSError as exc:
        return _shell_error_code(exc)
    try:
        returncode = process.wait(timeout=spec.runtime_max_sec)
    except subprocess.TimeoutExpired:
        _emit_diagnostic(
            {
                "event": "run_bounded_command_timeout",
                "backend": "portable_fallback",
                "runtime_max_sec": spec.runtime_max_sec,
                "term_grace_sec": term_grace_sec,
            }
        )
        _terminate_process_group(process, term_grace_sec=term_grace_sec)
        process.wait()
        return TIMEOUT_EXIT_CODE
    return _normalize_exit_code(returncode)


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

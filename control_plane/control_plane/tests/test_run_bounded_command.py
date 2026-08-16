from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest


def _load_launcher_module():
    script_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "run_bounded_command.py"
    )
    spec = importlib.util.spec_from_file_location("run_bounded_command_test_module", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_escaped_session_scripts(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    probe_pid_path = tmp_path / "probe.pid"
    grandchild_pid_path = tmp_path / "grandchild.pid"
    grandchild_script = tmp_path / "grandchild.py"
    probe_script = tmp_path / "probe.py"
    root_script = tmp_path / "root.py"
    grandchild_script.write_text(
        "import os, signal, sys, time\n"
        "from pathlib import Path\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='utf-8')\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    probe_script.write_text(
        "import os, signal, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "os.setsid()\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='utf-8')\n"
        "subprocess.Popen([sys.executable, sys.argv[2], sys.argv[3]])\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    root_script.write_text(
        "import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]])\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    return root_script, probe_script, grandchild_script, probe_pid_path, grandchild_pid_path


def _read_pid(path: Path, *, timeout_seconds: float = 5.0) -> int:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            return int(path.read_text(encoding="utf-8").strip())
        time.sleep(0.05)
    raise AssertionError(f"pid file was not written: {path}")


def _assert_process_gone(pid: int, *, timeout_seconds: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    raise AssertionError(f"process {pid} survived termination")


def test_parse_cli_requires_separator_and_payload() -> None:
    module = _load_launcher_module()

    with pytest.raises(SystemExit, match="missing `--` separator"):
        module.parse_cli(["--memory-max", "8G"])

    with pytest.raises(SystemExit, match="missing child command"):
        module.parse_cli(["--memory-max", "8G", "--"])


def test_parse_helpers_validate_sizes_quotas_and_runtime() -> None:
    module = _load_launcher_module()

    assert module._parse_size("8G") == 8 * 1024**3
    assert module._parse_size("512m") == 512 * 1024**2
    assert module._parse_cpu_quota_percent("300%") == 300.0
    assert module._parse_runtime_max_sec("4500") == 4500

    with pytest.raises(argparse.ArgumentTypeError):
        module._parse_size("7Q")
    with pytest.raises(argparse.ArgumentTypeError):
        module._parse_cpu_quota_percent("300")
    with pytest.raises(argparse.ArgumentTypeError):
        module._parse_tasks_max("0")
    with pytest.raises(argparse.ArgumentTypeError):
        module._parse_runtime_max_sec("-1")


def test_select_affinity_caps_by_cpu_quota() -> None:
    module = _load_launcher_module()

    assert module._select_affinity((3, 7, 9, 11), "300%") == (3, 7, 9)
    assert module._select_affinity((3, 7, 9, 11), "250%") == (3, 7, 9)
    assert module._select_affinity((3, 7), None) == (3, 7)


def test_apply_fallback_limits_sets_rlimits_and_affinity() -> None:
    module = _load_launcher_module()
    rlimit_calls: list[tuple[int, tuple[int, int]]] = []
    affinity_calls: list[tuple[int, tuple[int, ...]]] = []
    spec = module.LimitSpec(
        memory_high="6G",
        memory_max="8G",
        cpu_quota="300%",
        tasks_max=512,
        runtime_max_sec=1200,
    )

    selected = module._apply_fallback_limits(
        spec,
        allowed_cpus=(2, 4, 6, 8),
        setrlimit=lambda limit, value: rlimit_calls.append((limit, value)),
        sched_setaffinity=lambda pid, cpus: affinity_calls.append((pid, tuple(cpus))),
    )

    assert selected == (2, 4, 6)
    assert rlimit_calls == [
        (module.resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3)),
    ]
    assert affinity_calls == [(0, (2, 4, 6))]


def test_detect_systemd_user_manager_and_build_command(tmp_path: Path) -> None:
    module = _load_launcher_module()
    env = {
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/tmp/fake-bus",
        "XDG_RUNTIME_DIR": str(tmp_path),
    }
    recorded_commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        recorded_commands.append(list(command))
        return subprocess.CompletedProcess(command, 0, "", "")

    probe = module._detect_systemd_user_manager(
        env=env,
        which=lambda name: f"/usr/bin/{name}",
        run=fake_run,
    )
    spec = module.LimitSpec(
        memory_high="6G",
        memory_max="8G",
        cpu_quota="300%",
        tasks_max=512,
        runtime_max_sec=1200,
    )
    command = module._build_systemd_command(spec, ["python3", "child.py", "--flag"])

    assert probe.usable is True
    assert probe.reason == "systemd_run_scope_ok"
    assert recorded_commands == [["/usr/bin/systemd-run", "--user", "--scope", "--quiet", "/usr/bin/true"]]
    assert command == [
        "systemd-run",
        "--user",
        "--scope",
        "-p",
        "MemoryHigh=6G",
        "-p",
        "MemoryMax=8G",
        "-p",
        "CPUQuota=300%",
        "-p",
        "TasksMax=512",
        "-p",
        "RuntimeMaxSec=1200",
        "python3",
        "child.py",
        "--flag",
    ]


def test_main_uses_portable_fallback_when_systemd_binary_exists_without_user_bus(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_launcher_module()
    fallback_calls: list[list[str]] = []

    monkeypatch.setattr(module.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.delenv("DBUS_SESSION_BUS_ADDRESS", raising=False)
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(module.os, "sched_getaffinity", lambda pid: {0, 1, 2, 3})
    monkeypatch.setattr(
        module,
        "_run_portable_fallback",
        lambda spec, child_command, term_grace_sec=module._TERM_GRACE_SEC: (
            fallback_calls.append(list(child_command)) or 0
        ),
    )
    monkeypatch.setattr(
        module,
        "_run_systemd_command",
        lambda spec, child_command: pytest.fail("systemd backend should not be selected"),
    )

    result = module.main(["--memory-max", "8G", "--runtime-max-sec", "1200", "--", "python3", "-c", "print(1)"])

    captured = capsys.readouterr()
    assert result == 0
    assert fallback_calls == [["python3", "-c", "print(1)"]]
    assert '"backend": "portable_fallback"' in captured.err
    assert '"reason": "missing_env:DBUS_SESSION_BUS_ADDRESS,XDG_RUNTIME_DIR"' in captured.err


def test_run_portable_fallback_preserves_exit_code() -> None:
    module = _load_launcher_module()
    spec = module.LimitSpec(
        memory_high=None,
        memory_max=None,
        cpu_quota=None,
        tasks_max=None,
        runtime_max_sec=10,
    )

    result = module._run_portable_fallback(
        spec,
        [sys.executable, "-c", "import sys; sys.exit(7)"],
        term_grace_sec=0.1,
    )

    assert result == 7


def test_run_portable_fallback_normalizes_signal_exit() -> None:
    module = _load_launcher_module()
    spec = module.LimitSpec(
        memory_high=None,
        memory_max=None,
        cpu_quota=None,
        tasks_max=None,
        runtime_max_sec=10,
    )

    result = module._run_portable_fallback(
        spec,
        [sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGKILL)"],
        term_grace_sec=0.1,
    )

    assert result == 137


def test_run_portable_fallback_enforces_tasks_max_on_child_tree(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_launcher_module()
    grandchild_pid_path = tmp_path / "tasks-max-grandchild.pid"
    spec = module.LimitSpec(
        memory_high=None,
        memory_max=None,
        cpu_quota=None,
        tasks_max=1,
        runtime_max_sec=10,
    )
    child_code = (
        "import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, '-c', "
        "\"import os, pathlib, sys, time; pathlib.Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)\", "
        "sys.argv[1]])\n"
        "time.sleep(60)\n"
    )

    result = module._run_portable_fallback(
        spec,
        [sys.executable, "-c", child_code, str(grandchild_pid_path)],
        term_grace_sec=0.2,
    )

    captured = capsys.readouterr()
    assert result == module.TASKS_MAX_EXIT_CODE
    assert '"event": "run_bounded_command_tasks_max_exceeded"' in captured.err
    grandchild_pid = _read_pid(grandchild_pid_path)
    _assert_process_gone(grandchild_pid)


def test_run_portable_fallback_times_out_and_kills_process_group(tmp_path: Path) -> None:
    module = _load_launcher_module()
    pid_path = tmp_path / "grandchild.pid"
    spec = module.LimitSpec(
        memory_high=None,
        memory_max=None,
        cpu_quota=None,
        tasks_max=None,
        runtime_max_sec=1,
    )
    grandchild_code = (
        "import os, signal, sys, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "Path = __import__('pathlib').Path\n"
        "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='utf-8')\n"
        "time.sleep(60)\n"
    )
    parent_code = (
        "import signal, subprocess, sys, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "subprocess.Popen([sys.executable, '-c', sys.argv[2], sys.argv[1]])\n"
        "time.sleep(60)\n"
    )

    result = module._run_portable_fallback(
        spec,
        [sys.executable, "-c", parent_code, str(pid_path), grandchild_code],
        term_grace_sec=0.2,
    )

    assert result == module.TIMEOUT_EXIT_CODE
    grandchild_pid = int(pid_path.read_text(encoding="utf-8").strip())
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            os.kill(grandchild_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail(f"grandchild process {grandchild_pid} survived process-group timeout")


def test_launcher_sigterm_kills_descendant_new_session_tree(tmp_path: Path) -> None:
    launcher_path = Path(__file__).resolve().parents[2] / "scripts" / "run_bounded_command.py"
    root_script, probe_script, grandchild_script, probe_pid_path, grandchild_pid_path = (
        _write_escaped_session_scripts(tmp_path)
    )

    process = subprocess.Popen(
        [
            sys.executable,
            str(launcher_path),
            "--runtime-max-sec",
            "30",
            "--",
            sys.executable,
            str(root_script),
            str(probe_script),
            str(probe_pid_path),
            str(grandchild_script),
            str(grandchild_pid_path),
        ]
    )

    probe_pid = _read_pid(probe_pid_path)
    grandchild_pid = _read_pid(grandchild_pid_path)
    os.kill(process.pid, signal.SIGTERM)

    assert process.wait(timeout=10) == 128 + signal.SIGTERM
    _assert_process_gone(probe_pid)
    _assert_process_gone(grandchild_pid)

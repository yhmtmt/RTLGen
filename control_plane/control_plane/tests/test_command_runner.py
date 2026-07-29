"""Command runner callback robustness coverage."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import time

from control_plane.workers.command_runner import run_command_manifest


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
    raise AssertionError(f"process {pid} survived cancellation")


def test_command_runner_continues_when_cancel_callback_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        work_dir = Path(td) / "work"
        log_dir = Path(td) / "logs"
        work_dir.mkdir()
        calls = {"cancel": 0}

        def flaky_cancel() -> bool:
            calls["cancel"] += 1
            if calls["cancel"] == 1:
                raise RuntimeError("control-plane db temporarily unavailable")
            return False

        results = run_command_manifest(
            command_manifest=[
                {
                    "name": "write_output",
                    "run": "python3 -c \"from pathlib import Path; Path('done.txt').write_text('ok\\n')\"",
                }
            ],
            work_dir=str(work_dir),
            log_dir=str(log_dir),
            progress_interval_seconds=1,
            cancel_requested=flaky_cancel,
        )

        assert len(results) == 1
        assert results[0].returncode == 0
        assert (work_dir / "done.txt").read_text(encoding="utf-8") == "ok\n"
        assert calls["cancel"] >= 1


def test_command_runner_continues_when_progress_callback_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        work_dir = Path(td) / "work"
        log_dir = Path(td) / "logs"
        work_dir.mkdir()
        calls = {"progress": 0}

        def flaky_progress(_payload: dict) -> None:
            calls["progress"] += 1
            if calls["progress"] == 1:
                raise RuntimeError("control-plane db temporarily unavailable")

        results = run_command_manifest(
            command_manifest=[
                {
                    "name": "slow_output",
                    "run": (
                        "python3 -c \"import time; "
                        "print('start', flush=True); "
                        "time.sleep(1.5); "
                        "print('done', flush=True)\""
                    ),
                }
            ],
            work_dir=str(work_dir),
            log_dir=str(log_dir),
            progress_interval_seconds=1,
            on_command_progress=flaky_progress,
        )

        assert len(results) == 1
        assert results[0].returncode == 0
        assert calls["progress"] >= 1


def test_command_progress_reports_process_group_resources() -> None:
    with tempfile.TemporaryDirectory() as td:
        work_dir = Path(td) / "work"
        log_dir = Path(td) / "logs"
        work_dir.mkdir()
        progress: list[dict] = []

        results = run_command_manifest(
            command_manifest=[
                {
                    "name": "cpu_and_memory_probe",
                    "run": "python3 -c \"import time; sum(range(1000000)); time.sleep(1.5)\"",
                }
            ],
            work_dir=str(work_dir),
            log_dir=str(log_dir),
            progress_interval_seconds=1,
            on_command_progress=progress.append,
        )

        assert results[0].returncode == 0
        assert progress
        snapshot = progress[0]["process_group"]
        assert snapshot["process_group_id"] > 0
        assert snapshot["process_count"] >= 1
        assert snapshot["cpu_seconds"] >= 0
        assert snapshot["rss_bytes"] > 0
        assert any(member["command"] in {"bash", "python3"} for member in snapshot["processes"])


def test_command_runner_cancel_kills_descendant_new_session_tree() -> None:
    with tempfile.TemporaryDirectory() as td:
        work_dir = Path(td) / "work"
        log_dir = Path(td) / "logs"
        work_dir.mkdir()
        root_script, probe_script, grandchild_script, probe_pid_path, grandchild_pid_path = (
            _write_escaped_session_scripts(work_dir)
        )

        def cancel_requested() -> bool:
            return probe_pid_path.exists() and grandchild_pid_path.exists()

        results = run_command_manifest(
            command_manifest=[
                {
                    "name": "spawn_escape",
                    "run": (
                        f"python3 {root_script} {probe_script} {probe_pid_path} "
                        f"{grandchild_script} {grandchild_pid_path}"
                    ),
                }
            ],
            work_dir=str(work_dir),
            log_dir=str(log_dir),
            progress_interval_seconds=1,
            cancel_requested=cancel_requested,
        )

        assert len(results) == 1
        assert results[0].returncode == 130
        assert results[0].canceled is True
        _assert_process_gone(_read_pid(probe_pid_path))
        _assert_process_gone(_read_pid(grandchild_pid_path))

"""Command runner callback robustness coverage."""

from __future__ import annotations

from pathlib import Path
import tempfile

from control_plane.workers.command_runner import run_command_manifest


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

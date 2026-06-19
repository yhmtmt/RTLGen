from __future__ import annotations

from control_plane.cli import run_worker_daemon as cli
from control_plane.services.worker_daemon import WorkerDaemonResult


def test_run_worker_daemon_cli_persists_filter_and_source_capabilities(monkeypatch, tmp_path, capsys) -> None:
    captured = {}

    monkeypatch.setattr(cli, "build_engine", lambda _url: object())
    monkeypatch.setattr(cli, "create_all", lambda _engine: None)
    monkeypatch.setattr(cli, "build_session_factory", lambda _engine: object())
    monkeypatch.setattr(cli, "_service_repo_head", lambda _repo_root: "abc123")

    def fake_run_worker_daemon(session_factory, *, config, log_fn=None):
        captured["session_factory"] = session_factory
        captured["config"] = config
        return WorkerDaemonResult(poll_count=0, executed_items=0, no_work_polls=0, results=[])

    monkeypatch.setattr(cli, "run_worker_daemon", fake_run_worker_daemon)

    rc = cli.main(
        [
            "--database-url",
            "sqlite+pysqlite:///:memory:",
            "--repo-root",
            str(tmp_path),
            "--machine-key",
            "eval-daemon-test",
            "--capability-filter-json",
            '{"platform":"nangate45","flow":"openroad"}',
            "--capabilities-json",
            '{"custom":"value"}',
        ]
    )

    assert rc == 0
    config = captured["config"]
    assert config.worker.capability_filter == {"platform": "nangate45", "flow": "openroad"}
    assert config.worker.capabilities["platform"] == "nangate45"
    assert config.worker.capabilities["flow"] == "openroad"
    assert config.worker.capabilities["custom"] == "value"
    assert config.worker.capabilities["worker_source"] == {
        "repo_root": str(tmp_path.resolve()),
        "head": "abc123",
    }
    assert '"poll_count": 0' in capsys.readouterr().out

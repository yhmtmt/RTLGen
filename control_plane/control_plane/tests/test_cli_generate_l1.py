"""Top-level CLI coverage for Layer 1 generation flags."""

from __future__ import annotations

from unittest.mock import patch

from control_plane.cli.main import main


def test_generate_l1_sweep_cli_omitted_dependencies_remain_unspecified(monkeypatch) -> None:
    from control_plane.cli import generate_l1_sweep
    from control_plane.services.l1_task_generator import Layer1TaskGenerateResult

    class _SessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    captured = {}

    monkeypatch.setattr(generate_l1_sweep, "build_engine", lambda _database_url: object())
    monkeypatch.setattr(generate_l1_sweep, "create_all", lambda _engine: None)
    monkeypatch.setattr(generate_l1_sweep, "build_session_factory", lambda _engine: _SessionContext)

    def fake_generate(_session: object, request: object) -> Layer1TaskGenerateResult:
        captured["depends_on_item_ids"] = request.depends_on_item_ids
        return Layer1TaskGenerateResult(
            item_id="l1_demo",
            status="applied",
            work_item_id="wi",
            task_request_id="tr",
        )

    monkeypatch.setattr(generate_l1_sweep, "generate_l1_sweep_task", fake_generate)

    result = generate_l1_sweep.main(
        [
            "--database-url",
            "sqlite+pysqlite:///:memory:",
            "--repo-root",
            "/tmp/repo",
            "--sweep-path",
            "runs/designs/demo/sweep.json",
            "--configs",
            "runs/designs/demo/config.json",
            "--platform",
            "nangate45",
            "--out-root",
            "runs/designs/demo",
            "--item-id",
            "l1_demo",
            "--no-auto-dispatch",
        ]
    )

    assert result == 0
    assert captured["depends_on_item_ids"] is None


def test_top_level_generate_l1_forwards_extended_generation_flags() -> None:
    with patch("control_plane.cli.main.generate_l1_sweep_main", return_value=0) as generate:
        result = main(
            [
                "generate-l1-sweep",
                "--database-url",
                "sqlite+pysqlite:///:memory:",
                "--repo-root",
                "/repo",
                "--sweep-path",
                "sweep.json",
                "--configs",
                "a.json",
                "b.json",
                "--platform",
                "nangate45",
                "--out-root",
                "runs/designs/demo",
                "--make-target",
                "1_1_yosys_canonicalize",
                "--evaluation-mode",
                "measurement_only",
                "--abstraction-layer",
                "circuit_block",
                "--expected-direction",
                "lower_power",
                "--expected-reason",
                "shared datapath",
                "--comparison-role",
                "candidate_pnr",
                "--paired-baseline-item-id",
                "l1_baseline",
                "--depends-on-item-id",
                "l2_equivalence",
                "--requires-merged-inputs",
                "--requires-materialized-refs",
                "--acceptance-notes",
                "accept timing/flow failures as boundary evidence",
                "--trial-count",
                "3",
                "--seed-start",
                "100",
                "--stop-after-failures",
                "2",
                "--no-update-proposal-files",
            ]
        )

    assert result == 0
    forwarded = generate.call_args.args[0]
    configs_index = forwarded.index("--configs")
    assert forwarded[configs_index + 1 : configs_index + 3] == ["a.json", "b.json"]
    assert forwarded[forwarded.index("--make-target") + 1] == "1_1_yosys_canonicalize"
    assert forwarded[forwarded.index("--evaluation-mode") + 1] == "measurement_only"
    assert forwarded[forwarded.index("--abstraction-layer") + 1] == "circuit_block"
    assert forwarded[forwarded.index("--expected-direction") + 1] == "lower_power"
    assert forwarded[forwarded.index("--expected-reason") + 1] == "shared datapath"
    assert forwarded[forwarded.index("--comparison-role") + 1] == "candidate_pnr"
    assert forwarded[forwarded.index("--paired-baseline-item-id") + 1] == "l1_baseline"
    assert forwarded[forwarded.index("--depends-on-item-id") + 1] == "l2_equivalence"
    assert "--requires-merged-inputs" in forwarded
    assert "--requires-materialized-refs" in forwarded
    assert forwarded[forwarded.index("--acceptance-notes") + 1] == "accept timing/flow failures as boundary evidence"
    assert forwarded[forwarded.index("--trial-count") + 1] == "3"
    assert forwarded[forwarded.index("--seed-start") + 1] == "100"
    assert forwarded[forwarded.index("--stop-after-failures") + 1] == "2"
    assert "--no-update-proposal-files" in forwarded


def test_top_level_generate_l2_forwards_no_update_proposal_files() -> None:
    with patch("control_plane.cli.main.generate_l2_campaign_main", return_value=0) as generate:
        result = main(
            [
                "generate-l2-campaign",
                "--database-url",
                "sqlite+pysqlite:///:memory:",
                "--repo-root",
                "/repo",
                "--campaign-path",
                "campaign.json",
                "--item-id",
                "l2_item",
                "--no-run-physical",
                "--requires-materialized-refs",
                "--no-update-proposal-files",
            ]
        )

    assert result == 0
    forwarded = generate.call_args.args[0]
    assert forwarded[forwarded.index("--campaign-path") + 1] == "campaign.json"
    assert forwarded[forwarded.index("--item-id") + 1] == "l2_item"
    assert "--no-run-physical" in forwarded
    assert "--requires-materialized-refs" in forwarded
    assert "--no-update-proposal-files" in forwarded


def test_top_level_run_worker_forwards_only_worker_flags() -> None:
    with patch("control_plane.cli.main.run_worker_main", return_value=0) as worker:
        result = main(
            [
                "run-worker",
                "--database-url",
                "sqlite+pysqlite:///:memory:",
                "--repo-root",
                "/repo",
                "--machine-key",
                "eval-daemon",
                "--machine-role",
                "evaluator",
                "--slot-capacity",
                "1",
                "--max-items",
                "1",
            ]
        )

    assert result == 0
    forwarded = worker.call_args.args[0]
    assert "--source-update-ref" not in forwarded
    assert forwarded.count("--machine-role") == 1
    assert forwarded.count("--slot-capacity") == 1
    assert forwarded[forwarded.index("--machine-role") + 1] == "evaluator"
    assert forwarded[forwarded.index("--slot-capacity") + 1] == "1"

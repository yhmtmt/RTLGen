"""Top-level CLI coverage for Layer 1 generation flags."""

from __future__ import annotations

from unittest.mock import patch

from control_plane.cli.main import main


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
                "--trial-count",
                "3",
                "--seed-start",
                "100",
                "--stop-after-failures",
                "2",
            ]
        )

    assert result == 0
    forwarded = generate.call_args.args[0]
    configs_index = forwarded.index("--configs")
    assert forwarded[configs_index + 1 : configs_index + 3] == ["a.json", "b.json"]
    assert forwarded[forwarded.index("--make-target") + 1] == "1_1_yosys_canonicalize"
    assert forwarded[forwarded.index("--evaluation-mode") + 1] == "measurement_only"
    assert forwarded[forwarded.index("--abstraction-layer") + 1] == "circuit_block"
    assert forwarded[forwarded.index("--trial-count") + 1] == "3"
    assert forwarded[forwarded.index("--seed-start") + 1] == "100"
    assert forwarded[forwarded.index("--stop-after-failures") + 1] == "2"

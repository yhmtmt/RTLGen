#!/usr/bin/env python3
"""RTLGen coverage for staged EVENT_WAIT CQ decode."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _generate_top(tmp_path: Path, mode: str = "full") -> str:
    cfg = json.loads((REPO_ROOT / "npu/rtlgen/examples/minimal.json").read_text(encoding="utf-8"))
    cfg["enable_axi_lite_wrapper"] = False
    cfg["cq_mem_ablation_mode"] = mode
    cfg_path = tmp_path / f"{mode}.json"
    out_dir = tmp_path / mode
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    subprocess.run(
        [sys.executable, "npu/rtlgen/gen.py", "--config", str(cfg_path), "--out", str(out_dir)],
        cwd=REPO_ROOT,
        check=True,
    )
    return (out_dir / "top.v").read_text(encoding="utf-8")


def test_full_cq_event_wait_latches_id_before_stalling(tmp_path: Path) -> None:
    top = _generate_top(tmp_path)

    assert "reg [15:0] event_scoreboard_id [0:15];" in top
    assert "reg [15:0] event_scoreboard_valid;" in top
    assert "reg        event_wait_pending;" in top
    assert "reg [15:0] event_wait_id;" in top
    assert "event_wait_id <= cq_mem_rdata[47:32];" in top
    assert "event_wait_pending <= 1'b1;" in top
    assert "event_scoreboard_id[event_i] == event_wait_id" in top
    assert "event_scoreboard_valid[event_wait_match_slot] <= 1'b0;" in top
    assert "event_state" not in top


@pytest.mark.parametrize("mode", ["v1_softmax_event_only", "v1_event_wait_only", "v1_event_only"])
def test_event_wait_diagnostic_modes_use_staged_wait(tmp_path: Path, mode: str) -> None:
    top = _generate_top(tmp_path, mode)

    assert "event_wait_id <= cq_mem_rdata[47:32];" in top
    assert "if (event_wait_pending) begin" in top
    assert "event_scoreboard_id[event_i] == event_wait_id" in top
    assert "event_scoreboard_valid[event_wait_match_slot] <= 1'b0;" in top
    assert "event_state" not in top


def test_event_index_diagnostic_mode_uses_bounded_scoreboard(tmp_path: Path) -> None:
    top = _generate_top(tmp_path, "v1_event_index_only")

    assert "event_wait_id <= cq_mem_rdata[47:32];" not in top
    assert "event_scoreboard_id[event_i] == cq_mem_rdata[47:32]" in top
    assert "event_state" not in top

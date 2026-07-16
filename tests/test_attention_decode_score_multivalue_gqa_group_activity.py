from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from npu.eval.generate_attention_decode_score_multivalue_gqa_group_activity import (
    generate_phase_activity,
)


def _tool_available(name: str) -> bool:
    return shutil.which(name) is not None or (Path("/oss-cad-suite/bin") / name).exists()


def _config() -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_gqa_group_activity",
        "attention_decode_score_multivalue_gqa_group": {
            "max_blocks": 16384,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
            "query_heads_per_kv": 8,
        },
    }


def test_gqa_group_activity_smoke_uses_actual_wrapper_and_manifest(tmp_path: Path) -> None:
    if not _tool_available("iverilog") or not _tool_available("vvp"):
        pytest.skip("iverilog/vvp unavailable")

    manifest = generate_phase_activity(
        _config(), tmp_path, block_count=1, head_dim=3, clock_period_ns=10.0
    )
    manifest_path = tmp_path / "attention_decode_score_multivalue_gqa_group_activity_manifest.json"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert manifest["model"] == "decode_score_multivalue_gqa_group_phase_activity_v1"
    assert manifest["scope"] == "tb/dut"
    assert "complete generated GQA8 group wrapper" in manifest["scope_semantics"]
    assert manifest["query_heads_per_kv"] == 8
    assert manifest["clock_period_ns"] == 10.0
    assert manifest["phase_partition_cycle_sum"] == manifest["representative_full_transaction_cycles"]

    phases = {row["phase"]: row for row in manifest["phases"]}
    assert set(phases) == {"score_fill", "replay_value", "finalize_result"}
    assert phases["finalize_result"]["measured_cycles"] == 58208
    assert phases["finalize_result"]["scaling"]["query_heads_per_kv"] == 8
    for phase in phases.values():
        vcd = tmp_path / phase["vcd"]
        raw = vcd.read_bytes()
        assert raw
        assert phase["vcd_sha256"] == hashlib.sha256(raw).hexdigest()
        assert b"$scope module tb $end" in raw

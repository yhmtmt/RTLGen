from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from npu.eval.generate_attention_decode_score_multivalue_gqa_group_activity import (
    _query_lanes,
    generate_phase_activity,
)


def _tool_available(name: str) -> bool:
    return shutil.which(name) is not None or (Path("/oss-cad-suite/bin") / name).exists()


def _config(parallel_query_head_lanes: int | None = None) -> dict:
    return {
        "top_name": "attention_decode_score_multivalue_gqa_group_activity",
        "attention_decode_score_multivalue_gqa_group": {
            "max_blocks": 16384,
            "array_n": 8,
            "value_slices": 16,
            "divider_impl": "iterative_restoring",
            "score_scale_lanes_per_cycle": 1,
            "query_heads_per_kv": 8,
            **({"parallel_query_head_lanes": parallel_query_head_lanes} if parallel_query_head_lanes else {}),
        },
    }


@pytest.mark.parametrize(
    "parallel_query_head_lanes,waves,folded",
    [(8, 1, False), (4, 2, True), (2, 4, True), (1, 8, True)],
)
def test_gqa_group_activity_smoke_uses_actual_wrapper_and_manifest(
    tmp_path: Path, parallel_query_head_lanes: int, waves: int, folded: bool
) -> None:
    if not _tool_available("iverilog") or not _tool_available("vvp"):
        pytest.skip("iverilog/vvp unavailable")

    manifest = generate_phase_activity(
        _config(parallel_query_head_lanes), tmp_path, block_count=1, head_dim=3, clock_period_ns=10.0
    )
    manifest_path = tmp_path / "attention_decode_score_multivalue_gqa_group_activity_manifest.json"
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert manifest["model"] == "decode_score_multivalue_gqa_group_phase_activity_v1"
    assert manifest["scope"] == "tb/dut"
    if folded:
        assert "folded" in manifest["scope_semantics"]
        assert (
            manifest["semantic_profile"]
            == "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_folded_group_activity_v1"
        )
    else:
        assert "all eight query-head clusters" in manifest["scope_semantics"]
        assert (
            manifest["semantic_profile"]
            == "decode_m1x8_shared_score_16x8d_value_iterdiv_gqa8_group_activity_v1"
        )
    assert manifest["query_heads_per_kv"] == 8
    assert manifest["parallel_query_head_lanes"] == parallel_query_head_lanes
    assert manifest["query_head_waves"] == waves
    assert manifest["query_activity_profile"] == "eight_distinct_deterministic_signed_int8_query_lanes"
    assert manifest["clock_period_ns"] == 10.0
    assert manifest["phase_partition_cycle_sum"] == manifest["representative_full_transaction_cycles"]
    assert manifest["phases"][2]["scaling"]["query_head_waves"] == waves

    phases = {row["phase"]: row for row in manifest["phases"]}
    assert set(phases) == {"score_fill", "replay_value", "finalize_result"}
    if not folded:
        assert phases["finalize_result"]["measured_cycles"] == 58208
    assert phases["finalize_result"]["scaling"]["query_heads_per_kv"] == 8
    for phase in phases.values():
        vcd = tmp_path / phase["vcd"]
        raw = vcd.read_bytes()
        assert raw
        assert phase["vcd_sha256"] == hashlib.sha256(raw).hexdigest()
        assert b"$scope module tb $end" in raw


def test_query_activity_uses_distinct_signed_int8_lanes() -> None:
    lanes = _query_lanes(-127, 17)
    assert len(lanes) == 8
    assert len(set(lanes)) == 8
    assert all(-127 <= lane <= 127 for lane in lanes)

import copy
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import (
    compare_compositional_rows,
    compare_full_rows,
    expected_schedule_prefix,
)
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import _validate


def _design_dir() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_p54x8_p53x8_c16_r2_l8_b59"
    )


def _rtl_dir() -> Path:
    return _design_dir() / "verilog"


def _sample_rows() -> list[dict[str, object]]:
    return [
        {
            "command_id": 0x8200,
            "head_id": 3,
            "slice": 7,
            "last": False,
            "global_max": -11,
            "exp_sum": 991,
            "value": [3, -2, 7, 0, 19, -5, 4, 8],
        },
        {
            "command_id": 0x8200,
            "head_id": 3,
            "slice": 8,
            "last": False,
            "global_max": -8,
            "exp_sum": 1012,
            "value": [4, -1, 8, 1, 20, -4, 5, 9],
        },
    ]


def test_full_row_comparator_accepts_exact_rows_and_rejects_one_field_mismatch() -> None:
    expected = _sample_rows()
    exact = compare_full_rows(expected, copy.deepcopy(expected))
    assert exact["passed"] is True
    assert exact["first_mismatch"] is None

    mismatched = copy.deepcopy(expected)
    mismatched[1]["exp_sum"] = 1013
    rejected = compare_full_rows(expected, mismatched)
    assert rejected["passed"] is False
    assert rejected["first_mismatch"] == {
        "row": 1,
        "field": "exp_sum",
        "expected": 1012,
        "observed": 1013,
    }
    assert rejected["expected_hash"] != rejected["observed_hash"]


def test_compositional_comparator_requires_all_cluster_and_root_rows() -> None:
    cluster_rows = [[{"cluster": cluster, "value": cluster}] for cluster in range(16)]
    root_rows = [{"command_id": 1, "head_id": 0, "slice": 0, "last": True, "value": [1] * 16}]
    exact = compare_compositional_rows(
        expected_cluster_rows=cluster_rows,
        observed_cluster_rows=copy.deepcopy(cluster_rows),
        expected_root_rows=root_rows,
        observed_root_rows=copy.deepcopy(root_rows),
    )
    assert exact["passed"] is True

    observed_clusters = copy.deepcopy(cluster_rows)
    observed_clusters[9][0]["value"] = -1
    rejected = compare_compositional_rows(
        expected_cluster_rows=cluster_rows,
        observed_cluster_rows=observed_clusters,
        expected_root_rows=root_rows,
        observed_root_rows=root_rows,
    )
    assert rejected["passed"] is False
    assert rejected["clusters"][9]["first_mismatch"]["field"] == "value"


def test_schedule_prefix_is_group_major_and_wraps_cleanly() -> None:
    schedule = expected_schedule_prefix(command_count=12)
    assert schedule[:8] == ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7))
    assert schedule[8:12] == ((8, 0), (8, 1), (8, 2), (8, 3))
    assert expected_schedule_prefix(command_count=32)[31] == (24, 7)
    assert expected_schedule_prefix(command_count=33)[32] == (0, 0)


def test_checked_in_config_rejects_partition_drift() -> None:
    config = json.loads((_design_dir() / "config.json").read_text(encoding="utf-8"))
    _validate(config)
    body = config["attention_score32_exact_local16_global_tree_cluster_sram_gqa8"]
    body["cluster_producers"] = [54] * 7 + [53] * 9
    try:
        _validate(config)
    except SystemExit as exc:
        assert "exactly eight 54s followed by eight 53s" in str(exc)
    else:
        raise AssertionError("expected partition drift to be rejected")


def test_checked_in_top_removes_external_value_lanes_and_enforces_fill_window() -> None:
    manifest = json.loads(
        (_rtl_dir() / "attention_score32_exact_local16_global_tree_cluster_sram_gqa8_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    rtl = (_rtl_dir() / "top.v").read_text(encoding="utf-8")

    assert manifest["semantic_profile"] == "score32_exact_local16_global_tree_cluster_sram_gqa8_full_compute_v1"
    assert manifest["internal_value_memory_lanes"] == 1712
    assert manifest["external_fill_interfaces"] == 16
    assert manifest["service_model"]["per_cluster_internal_value_memory_lanes"] == [108] * 8 + [106] * 8
    assert "output wire [1711:0] value_read_req_valid" not in rtl
    assert "input  wire [876543:0] value_response_matrix" not in rtl
    assert "input  wire [15:0] fill_target_valid" in rtl
    assert "output wire [15:0] cluster_fill_schedule_contract_error" in rtl
    assert "output wire fill_schedule_contract_error" in rtl
    assert "assign fill_target_schedule_allowed_w[gfill] =" in rtl
    assert "fill_target_head_base[(gfill * 5) +: 5] == expected_head_base_w" in rtl
    assert "fill_target_head_base[(gfill * 5) +: 5] == next_expected_head_base_w" in rtl
    assert ".fill_target_valid(fill_target_valid[0] && fill_target_schedule_allowed_w[0])" in rtl
    assert "fill_target_valid[0] && (!fill_target_metadata_valid_w[0] || !fill_target_schedule_allowed_w[0])" in rtl

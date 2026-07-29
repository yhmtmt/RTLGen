import copy
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local16_global_tree_cluster_sram_gqa8 import (
    DEFAULT_ROOT_READY_PATTERN,
    DEFAULT_SUBPROCESS_TIMEOUT_SEC,
    EXPECTED_PER_CLUSTER,
    EXPECTED_TOTALS,
    TB_TIMEOUT_CYCLES,
    _evaluate_observations,
    _failure_classification,
    _fill_rows_for_wave,
    _testbench,
    compare_compositional_rows,
    compare_full_rows,
    expected_counts,
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


def test_generated_testbench_is_real_memh_backed_composed_traffic() -> None:
    tb = _testbench(
        top_name="attention_score32_exact_local16_global_tree_cluster_sram_gqa8_test",
    )

    assert 'localparam integer CLUSTERS = 16;' in tb
    assert 'localparam integer WAVES = 8;' in tb
    assert 'localparam integer TOTAL_PRODUCERS = 856;' in tb
    assert 'localparam integer TB_TIMEOUT_CYCLES = 50000;' in tb
    assert '$readmemh("query.memh", query_mem);' in tb
    assert '$readmemh("key.memh", key_mem);' in tb
    assert '$readmemh("fill.memh", fill_mem);' in tb
    assert "input_valid[producer_index] = 1'b1;" in tb
    assert "input_query[(producer_index * 128) +: 128] = query_mem[flat_index];" in tb
    assert "input_key[(producer_index * 128) +: 128] = key_mem[flat_index];" in tb
    assert "input_valid[producer_index] && input_ready[producer_index]" in tb
    assert "$countones(input_valid & input_ready)" in tb
    assert "fill_target_valid[cluster_index] = 1'b1;" in tb
    assert "fill_target_buffer_sel[cluster_index] = fill_wave[cluster_index][0];" in tb
    assert "fill_valid[cluster_index] = 1'b1;" in tb
    assert "fill_data[(cluster_index * 512) +: 512] = fill_mem[fill_flat_index];" in tb
    assert "fill_target_valid[cluster_index] && fill_target_ready[cluster_index]" in tb
    assert "fill_valid[cluster_index] && fill_ready[cluster_index]" in tb
    assert "(fill_wave[cluster_index] < 2)" in tb
    assert "fill_wave[cluster_index] <= (expected_wave_index + 1'b1)" in tb
    assert "command_id = 16'h8200;" in tb
    assert "command_head_base = 5'd0;" in tb
    assert "issued_commands < WAVES" in tb
    assert "dut.cluster_out_valid_w" in tb
    assert "dut.cluster_out_ready_w" in tb
    assert "ROOT_RESULT" in tb
    assert "CLUSTER_RESULT" in tb
    assert "if (cycle >= TB_TIMEOUT_CYCLES)" in tb
    assert "root_ready_mem[0] = 1'b1;" in tb
    assert "root_ready_mem[1] = 1'b1;" in tb
    assert "root_ready_mem[2] = 1'b0;" in tb
    assert "root_ready_mem[3] = 1'b1;" in tb


def test_fill_sidecar_layout_uses_exact_p54_and_p53_block_slots(monkeypatch: Any) -> None:
    def fake_value_blocks(*, producer: int, block_count: int, **_: object) -> tuple[object, ...]:
        return tuple(
            tuple(
                tuple(
                    tuple((producer * 2) + block for _lane in range(8))
                    for _row in range(8)
                )
                for _slice in range(16)
            )
            for block in range(block_count)
        )

    monkeypatch.setattr(
        "npu.eval.probe_attention_score32_exact_local16_global_tree_gqa8._value_blocks",
        fake_value_blocks,
    )
    p54 = _fill_rows_for_wave(cluster=0, wave=0)
    p53 = _fill_rows_for_wave(cluster=8, wave=0)

    assert len(p54) == 2048
    assert len(p53) == 2048
    low_byte = lambda rows, slot: rows[slot * 16] & 0xFF
    assert [low_byte(p54, slot) for slot in (0, 1, 18, 19, 20)] == [0, 1, 18, 19, 20]
    assert [low_byte(p53, slot) for slot in (0, 1, 20, 21, 22)] == [0, 1, 20, 21, 22]


def _audit_fixture() -> tuple[
    dict[str, object],
    dict[str, int],
    list[dict[str, int]],
    list[list[dict[str, object]]],
    list[dict[str, object]],
]:
    cluster_rows = [[{"cluster": cluster, "value": [cluster]}] for cluster in range(16)]
    root_rows = [{"command_id": 0x8200, "value": [1] * 16}]
    reference: dict[str, object] = {
        "cluster_rows": copy.deepcopy(cluster_rows),
        "root_rows": copy.deepcopy(root_rows),
        "cluster_hashes": ["expected"] * 16,
        "root_hash": "expected",
    }
    summary = dict(EXPECTED_TOTALS)
    summary.update(
        {
            "command_accept_count": 8,
            "cadence_command_accept_count": 8,
            "protocol_error": 0,
        }
    )
    cluster_summaries = [
        {"cluster": cluster, **EXPECTED_PER_CLUSTER, "errors": 0}
        for cluster in range(16)
    ]
    return reference, summary, cluster_summaries, cluster_rows, root_rows


def test_observation_evaluator_validates_every_exact_total_and_row() -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    result = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=root_rows,
    )
    assert result["passed"] is True
    assert result["classification"] == "passed"
    assert result["counts_passed"] is True
    assert "observed_cluster_rows" not in result
    assert "expected_cluster_rows" not in result
    assert "observed_root_rows" not in result
    assert "expected_root_rows" not in result
    assert expected_counts()["totals"] == {
        "fill_target_accept_count": 128,
        "fill_row_accept_count": 262144,
        "producer_handshake_count": 8192,
        "sram_request_accept_count": 262144,
        "sram_response_accept_count": 262144,
        "cluster_row_count": 2048,
        "root_row_count": 128,
    }
    assert expected_counts()["per_cluster"][0] == {
        "wave_command_accept_count": 8,
        "completed_command_count": 1,
        "emitted_beat_count": 128,
        "fill_target_accept_count": 8,
        "fill_row_accept_count": 16384,
        "request_accept_count": 16384,
        "response_accept_count": 16384,
        "command_accept_count": 8,
        "command_release_count": 8,
    }


def test_observation_evaluator_rejects_incomplete_and_mismatched_rows_conclusively() -> None:
    reference, summary, cluster_summaries, cluster_rows, root_rows = _audit_fixture()
    incomplete = copy.deepcopy(cluster_rows)
    incomplete[4] = []
    incomplete_result = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=incomplete,
        observed_root_rows=root_rows,
    )
    assert incomplete_result["passed"] is False
    assert incomplete_result["classification"] == "failed_conclusive"
    assert incomplete_result["full_row_audit"]["clusters"][4]["first_mismatch"]["field"] == "__row_count__"

    mismatched_root = copy.deepcopy(root_rows)
    mismatched_root[0]["value"][7] = 2
    mismatch_result = _evaluate_observations(
        reference=reference,
        summary=summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=mismatched_root,
    )
    assert mismatch_result["passed"] is False
    assert mismatch_result["classification"] == "failed_conclusive"
    assert mismatch_result["full_row_audit"]["root"]["first_mismatch"]["field"] == "value"

    protocol_summary = dict(summary)
    protocol_summary["protocol_error"] = 1
    protocol_result = _evaluate_observations(
        reference=reference,
        summary=protocol_summary,
        cluster_summaries=cluster_summaries,
        observed_cluster_rows=cluster_rows,
        observed_root_rows=root_rows,
    )
    assert protocol_result["passed"] is False
    assert protocol_result["classification"] == "failed_conclusive"


def test_failure_classification_marks_timeouts_oom_and_kills_inconclusive() -> None:
    assert DEFAULT_ROOT_READY_PATTERN == (True, True, False, True)
    assert TB_TIMEOUT_CYCLES == 50000
    assert DEFAULT_SUBPROCESS_TIMEOUT_SEC == 900
    for returncode in (124, 125, 137, -9):
        assert _failure_classification(
            simulation_status="run_failed",
            returncode=returncode,
            stderr="",
            tb_timeout_cycle=None,
            passed=False,
        ) == "failed_inconclusive"
    assert _failure_classification(
        simulation_status="resource_failure",
        returncode=1,
        stderr="out of memory",
        tb_timeout_cycle=None,
        passed=False,
    ) == "failed_inconclusive"
    assert _failure_classification(
        simulation_status="ok",
        returncode=0,
        stderr="",
        tb_timeout_cycle=50000,
        passed=False,
    ) == "failed_inconclusive"


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

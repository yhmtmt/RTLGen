import copy
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local16_global_tree_gqa8 import (
    _default_config,
    _expected_cluster_summary_counts,
    _hierarchy_driver_data,
    _logical_commands,
    _resolve_workload,
    _testbench,
    _wave_command_schedule,
    compare_compositional_rows,
    compare_full_rows,
)
from npu.rtlgen.gen_attention_score32_exact_local16_global_tree_gqa8 import _validate
from npu.sim.perf.attention_exact_partial import LOCAL_TEMPORAL_WAVES


def _config_path() -> Path:
    return (
        REPO_ROOT
        / "runs"
        / "designs"
        / "npu_blocks"
        / "attention_score32_exact_local16_global_tree_gqa8_p54x8_p53x8_c16_r2_l8_b59"
        / "config.json"
    )


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


def test_hierarchy_config_rejects_any_instance_count_drift() -> None:
    config = json.loads(_config_path().read_text(encoding="utf-8"))
    _validate(config)
    body = config["attention_score32_exact_local16_global_tree_gqa8"]
    body["cluster_producers"] = [54] * 7 + [53] * 9
    with pytest.raises(SystemExit, match="exactly eight 54s followed by eight 53s"):
        _validate(config)


def _cluster_producers() -> tuple[int, ...]:
    return tuple([54] * 8 + [53] * 8)


def _workload(*, head_bases: tuple[int, ...] = (0,), seed: int = 29) -> dict[str, object]:
    config = _default_config()
    return _resolve_workload(
        config,
        command_count=len(head_bases),
        head_bases=head_bases,
        seed=seed,
    )


def test_wave_schedule_expands_each_logical_head_group_into_eight_transactions() -> None:
    workload = _workload(head_bases=(0, 8, 16, 24))
    logical = _logical_commands(workload)
    waves = _wave_command_schedule(workload)

    assert [command["command_id"] for command in logical] == [0x8200, 0x8201, 0x8202, 0x8203]
    assert len(waves) == len(logical) * LOCAL_TEMPORAL_WAVES
    for logical_index, command in enumerate(logical):
        group_waves = waves[logical_index * LOCAL_TEMPORAL_WAVES : (logical_index + 1) * LOCAL_TEMPORAL_WAVES]
        assert [entry["wave_index"] for entry in group_waves] == list(range(LOCAL_TEMPORAL_WAVES))
        assert all(entry["command_id"] == command["command_id"] for entry in group_waves)
        assert all(entry["head_base"] == command["head_base"] for entry in group_waves)
        assert all(entry["logical_index"] == logical_index for entry in group_waves)


def test_hierarchy_driver_populates_all_producer_and_value_lanes() -> None:
    driver = _hierarchy_driver_data(_cluster_producers(), _workload())

    assert len(driver["query_mem"]) == 856
    assert len(driver["key_mem"]) == 856
    assert len(driver["last_mem"]) == 856
    assert len(driver["value_mem"]) == 1712
    assert driver["max_beats_per_producer"] == 16
    assert driver["max_blocks_per_producer"] == 16
    assert all(len(stream) > 0 for stream in driver["query_mem"])
    assert all(len(stream) > 0 for stream in driver["value_mem"])
    assert all(limit > 0 for limit in driver["beat_limits"][-1])


def test_hierarchy_driver_rotates_p54_and_p53_extra_blocks_by_head_group() -> None:
    driver = _hierarchy_driver_data(_cluster_producers(), _workload(head_bases=(0, 8, 16, 24)))
    group0 = driver["command_block_counts"][0]
    group1 = driver["command_block_counts"][8]
    group2 = driver["command_block_counts"][16]
    group3 = driver["command_block_counts"][24]
    p53_base = 8 * 54

    assert group0[:10] == [2] * 10
    assert group0[10:54] == [1] * 44
    assert group1[10:20] == [2] * 10
    assert group2[20:30] == [2] * 10
    assert group3[30:40] == [2] * 10

    assert group0[p53_base : p53_base + 11] == [2] * 11
    assert group0[p53_base + 11 : p53_base + 53] == [1] * 42
    assert group1[p53_base + 11 : p53_base + 22] == [2] * 11
    assert group2[p53_base + 22 : p53_base + 33] == [2] * 11
    assert group3[p53_base + 33 : p53_base + 44] == [2] * 11


def test_cluster_summary_counts_match_group_major_wave_schedule() -> None:
    counts = _expected_cluster_summary_counts(_workload(head_bases=(0, 8, 16, 24)))
    assert counts == {
        "wave_command_accept_count": 32,
        "emitted_beat_count": 512,
        "completed_command_count": 4,
    }


def test_generated_testbench_drives_real_interfaces_and_wave_schedule() -> None:
    config = _default_config()
    workload = _workload()
    tb = _testbench(
        top_name=str(config["top_name"]),
        cluster_producers=_cluster_producers(),
        workload=workload,
        output_ready_pattern=(True,),
    )

    assert "localparam integer WAVE_COMMANDS = 8;" in tb
    assert "reg [31:0] cmd_beat_limit_mem [0:WAVE_COMMANDS-1][0:TOTAL_PRODUCERS-1];" in tb
    assert "if (rst_n && (active_command_index >= 0) && (beat_issue[producer_index] < cmd_beat_limit_mem[active_command_index][producer_index])) begin" in tb
    assert "input_valid[producer_index] = 1'b1;" in tb
    assert "if (value_read_req_valid[lane_index] && value_read_req_ready[lane_index]) begin" in tb
    assert "value_response_valid[lane_index] <= 1'b1;" in tb
    assert 'COMMAND_ACCEPT idx=%0d cmd=%0d head_base=%0d logical=%0d wave=%0d cycle=%0d' in tb

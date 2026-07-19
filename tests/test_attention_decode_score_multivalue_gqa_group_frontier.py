from __future__ import annotations

import json
from pathlib import Path

import pytest

from npu.eval.audit_attention_decode_score_multivalue_gqa_group_frontier import (
    _pareto,
    build_report,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    source = _write(
        tmp_path / "source.json",
        {
            "source_schedule": {
                "hidden_size": 4096,
                "attention_heads": 32,
                "kv_heads": 4,
                "sequence_length": 131072,
                "clock_ns": 6.0,
                "layers": 32,
                "compute_budget_um2": 400_000_000,
                "logic_area_used_um2": 399_000_000,
                "compute_area_um2": 396_000_000,
                "measured_shared_sram_used_area_um2": 240_000_000,
                "measured_tile_local_sram_area_um2": 40_000_000,
                "command_dispatch_cycles": 2,
                "kv_write_cycles": 10,
            }
        },
    )
    middle = _write(
        tmp_path / "middle.json",
        {"inputs": {"prior_frontier_json": source.name}},
    )
    prior = _write(
        tmp_path / "prior.json",
        {
            "inputs": {"prior_frontier_json": middle.name},
            "dense_qkv_tile": {"area_um2": 10_000, "effective_macs_per_cycle": 8.0},
            "best_throughput_candidate": {
                "candidate_id": "prior_best",
                "token_throughput_per_s": 100.0,
            },
        },
    )
    activity = _write(
        tmp_path / "group-activity.json",
        {
            "model": "decoder_attention_decode_score_multivalue_gqa_group_activity_power_v1",
            "decision": "activity_backed_gqa_group_power_measured",
            "promotion_gate_pass": True,
            "best_candidate_id": "gqa-group",
            "energy_scope": "one GQA8 group full-context decode attention command",
            "activity_contract": {"clock_period_ns": 8.0, "query_heads_per_kv": 8},
            "equivalence": {
                "equivalence_pass": True,
                "decision": "llama7b_gqa8_shared_kv_equivalence_pass",
                "query_heads_per_kv": 8,
                "parallel_query_head_lanes": 8,
                "query_head_waves": 1,
                "expected_group_result_sha256": "same-hash",
                "observed_group_result_sha256": "same-hash",
            },
            "best": {
                "candidate_id": "gqa-group",
                "status": "activity_backed",
                "flow_variant": "group_die7200",
                "ppa_metric": {"instance_area_um2": 2_000_000, "critical_path_ns": 7.5},
                "direct_group_full_context_energy_j": 0.014,
                "activity_power": {
                    "promotion_gate_pass": True,
                    "clock_period_ns": 8.0,
                    "full_context_cycles": 300,
                    "full_context_energy_j": 0.014,
                },
            },
        },
    )
    return prior, activity


def _lane_activity(
    tmp_path: Path, lanes: int, *, cycles: int, direct_energy: float
) -> Path:
    return _write(
        tmp_path / f"group-activity-l{lanes}.json",
        {
            "model": "decoder_attention_decode_score_multivalue_gqa_group_activity_power_v1",
            "decision": "activity_backed_gqa_group_power_measured",
            "promotion_gate_pass": True,
            "best_candidate_id": f"gqa-group-l{lanes}",
            "energy_scope": "one GQA8 group full-context decode attention command",
            "activity_contract": {"clock_period_ns": 8.0, "query_heads_per_kv": 8},
            "equivalence": {
                "equivalence_pass": True,
                "decision": "llama7b_gqa8_shared_kv_equivalence_pass",
                "query_heads_per_kv": 8,
                "parallel_query_head_lanes": lanes,
                "query_head_waves": 8 // lanes,
                "expected_group_result_sha256": "same-hash",
                "observed_group_result_sha256": "same-hash",
            },
            "best": {
                "candidate_id": f"gqa-group-l{lanes}",
                "status": "activity_backed",
                "flow_variant": f"group_die7200_l{lanes}",
                "ppa_metric": {"instance_area_um2": 2_000_000, "critical_path_ns": 7.5},
                "direct_group_full_context_energy_j": direct_energy,
                "activity_power": {
                    "promotion_gate_pass": True,
                    "clock_period_ns": 8.0,
                    "full_context_cycles": cycles,
                    "full_context_energy_j": direct_energy,
                },
            },
        },
    )


def test_recost_uses_four_logical_groups_and_recursive_measured_evidence(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    report = build_report(
        prior_frontier_json=prior,
        activity_power_json=activity,
        group_counts=[1, 2, 4],
    )

    rows = {row["group_count"]: row for row in report["rows"]}
    assert report["inputs"]["source_schedule_json"].endswith("source.json")
    assert report["inputs"]["group_activity_power_json"] == str(activity)
    assert report["schedule_contract"]["group_full_context_cycles_by_lanes"] == {"8": 300}
    assert rows[1]["parallel_query_head_lanes"] == 8
    assert rows[1]["query_head_waves"] == 1
    assert report["schedule_contract"]["query_heads_per_kv"] == 8
    assert report["schedule_contract"]["logical_groups_per_layer"] == 4
    assert rows[1]["group_waves_per_layer"] == 4
    assert rows[2]["group_waves_per_layer"] == 2
    assert rows[4]["group_waves_per_layer"] == 1
    assert rows[1]["attention_cycles"] == 1200
    assert rows[4]["attention_cycles"] == 300
    assert rows[1]["dense_qkv_tile_count"] == 640
    assert rows[1]["qkv_cycles"] == 4096
    assert rows[1]["clock_ns"] == 8.0
    assert rows[1]["group_area_mm2"] == pytest.approx(2.0)
    assert rows[4]["group_area_mm2"] == pytest.approx(8.0)
    assert rows[1]["gqa_group_component_energy_j_per_token"] == pytest.approx(1.792)
    assert rows[1]["gqa_group_component_energy_j_per_token"] == pytest.approx(
        rows[4]["gqa_group_component_energy_j_per_token"]
    )
    assert report["precision"]["status"] == "exact"
    assert report["precision"]["quality_change"] == "none_exact_integer_semantics_preserved"
    assert report["comparison_to_prior_best"]["available"] is True
    assert report["comparison_to_prior_best"]["prior_candidate_id"] == "prior_best"
    assert {row["group_count"] for row in report["pareto_rows"]} == {1, 2, 4}


def test_recost_cartesian_lane_activity_reports_generate_wave_and_cycle_formulas(tmp_path: Path) -> None:
    prior, _ = _inputs(tmp_path)
    lane_activity = {
        lanes: _lane_activity(tmp_path, lanes, cycles=cycles, direct_energy=0.010 * (8 / lanes))
        for lanes, cycles in {1: 320, 2: 160, 4: 120}.items()
    }
    report = build_report(
        prior_frontier_json=prior,
        lane_activity=lane_activity,
        group_counts=[1, 2, 4],
    )
    rows_by_key = {(row["parallel_query_head_lanes"], row["group_count"]): row for row in report["rows"]}
    assert len(rows_by_key) == 9
    assert report["schedule_contract"]["group_full_context_cycles_by_lanes"] == {
        "1": 320,
        "2": 160,
        "4": 120,
    }

    kv_heads = 4
    layers = 32
    for lanes in (1, 2, 4):
        for group_count in (1, 2, 4):
            row = rows_by_key[(lanes, group_count)]
            row_cycles = {
                1: 320,
                2: 160,
                4: 120,
            }[lanes]
            row_energy = {
                1: 0.08,
                2: 0.04,
                4: 0.02,
            }[lanes]
            expected_waves = kv_heads // group_count
            expected_attention = expected_waves * row_cycles
            assert row["group_waves_per_layer"] == expected_waves
            assert row["attention_cycles"] == expected_attention
            assert row["query_head_waves"] == 8 // lanes
            expected_id = f"decode_score_multivalue_gqa_group_l{lanes}_g{group_count}"
            assert row["candidate_id"] == expected_id
            expected_energy = 4 * 32 * row_energy
            assert row["gqa_group_component_energy_j_per_token"] == pytest.approx(expected_energy)
            assert row["parallel_query_head_lanes"] == lanes


def test_recost_requires_promoted_complete_gqa8_group(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    payload["promotion_gate_pass"] = False
    activity.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="promotion gate"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, group_counts=[1])

    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    payload["equivalence"]["query_heads_per_kv"] = 4
    activity.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="equivalence"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, group_counts=[1])

    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    payload["best"]["activity_power"]["promotion_gate_pass"] = False
    activity.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="activity power"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, group_counts=[1])


def test_recost_rejects_wrong_activity_model_and_unsupported_counts(tmp_path: Path) -> None:
    prior, activity = _inputs(tmp_path)
    payload = json.loads(activity.read_text(encoding="utf-8"))
    payload["model"] = "unrelated_activity_model"
    activity.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="model contract"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, group_counts=[1])

    prior, activity = _inputs(tmp_path)
    with pytest.raises(ValueError, match="unsupported group counts"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, group_counts=[3])
    with pytest.raises(ValueError, match="unique"):
        build_report(prior_frontier_json=prior, activity_power_json=activity, group_counts=[1, 1])


def test_pareto_filters_infeasible_and_dominated_rows() -> None:
    def row(candidate: str, latency: float, area: float, energy: float, *, fit: bool = True) -> dict:
        return {
            "candidate_id": candidate,
            "latency_us": latency,
            "embodied_logic_plus_shared_sram_area_mm2": area,
            "gqa_group_component_energy_mj_per_token": energy,
            "compute_budget_area_fit": fit,
            "timing_feasible": True,
        }

    rows = [
        row("fast", 1.0, 3.0, 2.0),
        row("small", 2.0, 1.0, 2.0),
        row("dominated", 2.0, 2.0, 2.0),
        row("infeasible", 0.5, 0.5, 0.5, fit=False),
    ]
    assert [candidate["candidate_id"] for candidate in _pareto(rows)] == ["fast", "small"]

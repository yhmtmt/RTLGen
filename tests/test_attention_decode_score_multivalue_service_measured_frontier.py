from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_attention_decode_score_multivalue_service_measured_frontier import (
    build_report,
)


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _source_schedule(tmp_path: Path, *, sequence_length: int = 131072) -> Path:
    return _write(
        tmp_path / "source_schedule.json",
        {
            "source_schedule": {
                "hidden_size": 4096,
                "attention_heads": 32,
                "kv_heads": 4,
                "sequence_length": sequence_length,
                "clock_ns": 6.0,
                "layers": 32,
                "compute_budget_um2": 12_000_000,
                "logic_area_used_um2": 4_000_000,
                "compute_area_um2": 3_000_000,
                "measured_shared_sram_used_area_um2": 2_000_000,
                "measured_tile_local_sram_area_um2": 1_000_000,
                "command_dispatch_cycles": 2,
                "kv_write_cycles": 10,
            }
        },
    )


def _workload_contract() -> dict:
    return {
        "command_block_count": 3,
        "context_tokens_per_block": 8,
        "active_context_tokens": 24,
        "max_blocks": 16,
        "max_context_capacity_tokens": 128,
        "value_dim": 128,
    }


def _result_semantics(result_mode: str) -> dict:
    return {
        "result_mode": result_mode,
        "supports_sequence_window_composition": result_mode == "exact_partial",
        "composition_scope": (
            "exact_partial_across_sequence_windows_before_finalization"
            if result_mode == "exact_partial"
            else "normalized_final_output_not_sequence_window_composable"
        ),
    }


def _prior_frontier(tmp_path: Path, *, sequence_length: int = 131072) -> Path:
    source = _source_schedule(tmp_path, sequence_length=sequence_length)
    linked_prior = _write(
        tmp_path / "linked_local_cluster_frontier.json",
        {
            "inputs": {
                "source_schedule_json": str(source),
            }
        },
    )
    rows = [
        {
            "candidate_id": "decode_score_multivalue_cluster_c1",
            "cluster_count": 1,
            "head_commands_per_layer": 32,
            "cluster_waves_per_layer": 32,
            "service_no_stall_full_context_cycles_per_wave": 320,
            "service_calibrated_full_context_cycles_per_wave": 400,
            "service_calibration_case_id": "c1_p128_b4_rr",
            "service_calibration_microkernel_no_stall_completion_cycle": 128,
            "service_calibration_microkernel_integrated_completion_cycle": 160,
            "dense_qkv_tile_count": 3,
            "dense_qkv_useful_parallelism_limit": 640,
            "qkv_cycles": 683,
            "attention_cycles": 12800,
            "fixed_cycles": 12,
            "layer_cycles": 13495,
            "total_cycles": 431840,
            "clock_ns": 8.0,
            "latency_us": 3454.72,
            "token_throughput_per_s": 289.459,
            "cluster_area_mm2": 2.0,
            "dense_qkv_area_mm2": 6.0,
            "retained_noncompute_logic_area_mm2": 1.0,
            "compute_budget_slack_mm2": 3.0,
            "logic_area_mm2": 9.0,
            "embodied_logic_plus_shared_sram_area_mm2": 12.0,
            "compute_budget_area_fit": True,
            "timing_feasible": True,
            "attention_cluster_dynamic_energy_mj_per_token": 1.0,
            "attention_cluster_service_window_leakage_energy_mj_per_token": 0.1,
            "attention_cluster_modeled_service_energy_mj_per_token": 1.1,
            "energy_lower_bound_component_estimate": True,
            "energy_status": "activity_backed_cluster_dynamic_plus_service_window_leakage_lower_bound_component_estimate_total_token_energy_incomplete",
        },
        {
            "candidate_id": "decode_score_multivalue_cluster_c2",
            "cluster_count": 2,
            "head_commands_per_layer": 32,
            "cluster_waves_per_layer": 16,
            "service_no_stall_full_context_cycles_per_wave": 320,
            "service_calibrated_full_context_cycles_per_wave": 440,
            "service_calibration_case_id": "c2_p128_b4_rr",
            "service_calibration_microkernel_no_stall_completion_cycle": 128,
            "service_calibration_microkernel_integrated_completion_cycle": 8863,
            "dense_qkv_tile_count": 3,
            "dense_qkv_useful_parallelism_limit": 640,
            "qkv_cycles": 683,
            "attention_cycles": 7040,
            "fixed_cycles": 12,
            "layer_cycles": 7735,
            "total_cycles": 247520,
            "clock_ns": 8.0,
            "latency_us": 1980.16,
            "token_throughput_per_s": 505.0,
            "cluster_area_mm2": 4.0,
            "dense_qkv_area_mm2": 6.0,
            "retained_noncompute_logic_area_mm2": 1.0,
            "compute_budget_slack_mm2": 1.0,
            "logic_area_mm2": 11.0,
            "embodied_logic_plus_shared_sram_area_mm2": 14.0,
            "compute_budget_area_fit": True,
            "timing_feasible": True,
            "attention_cluster_dynamic_energy_mj_per_token": 1.0,
            "attention_cluster_service_window_leakage_energy_mj_per_token": 0.2,
            "attention_cluster_modeled_service_energy_mj_per_token": 1.2,
            "energy_lower_bound_component_estimate": True,
            "energy_status": "activity_backed_cluster_dynamic_plus_service_window_leakage_lower_bound_component_estimate_total_token_energy_incomplete",
        },
    ]
    return _write(
        tmp_path / "prior_frontier.json",
        {
            "model": "decoder_attention_decode_score_multivalue_cluster_frontier_llama7b_v1",
            "decision": "shared_score_multivalue_cluster_measured_component_frontier_promoted",
            "promotion_status": "component_frontier_promoted_full_architecture_promotion_blocked",
            "item_id": "l2_decoder_attention_decode_score_multivalue_cluster_frontier_llama7b_v1_r1",
            "inputs": {"prior_frontier_json": str(linked_prior)},
            "schedule_contract": {
                "hidden_size": 4096,
                "attention_heads": 32,
                "kv_heads": 4,
                "head_dim": 128,
                "sequence_length": sequence_length,
                "layers": 32,
                "full_head_commands_per_layer": 32,
                "full_head_command_cycles_no_stall_baseline": 320,
                "full_head_phase_cycles_no_stall_baseline": {"fill": 200, "replay": 120},
                "sequence_sharding_supported": False,
            },
            "service_cycle_calibration": {
                "probe_contract": {
                    **_workload_contract(),
                    "consumed_case_ids": ["c1_p128_b4_rr", "c2_p128_b4_rr"],
                    "resource_policy": {
                        "packet_w": 128,
                        "banks": 4,
                        "req_queue_depth": 4,
                        "resp_queue_depth": 4,
                        "bank_queue_depth": 4,
                        "read_latency": 2,
                        "arb_mode": "round_robin",
                        "locality_burst_max": 2,
                    },
                }
            },
            "dense_qkv_tile": {"area_um2": 2_000_000, "effective_macs_per_cycle": 10240.0},
            "precision": {
                "status": "unchanged_integer_contract_from_merged_multivalue_equivalence",
                "equivalence_pass": True,
                "decision": "decode_score_multivalue_cluster_equivalence_pass",
                "score_tensor_hash": "score-hash",
                "final_tensor_hash": "final-hash",
                "quality_change": "none_exact_integer_semantics_preserved",
            },
            "rows": rows,
        },
    )


def _service_activity_power(tmp_path: Path, *, result_mode: str | None = "exact_partial") -> Path:
    return _write(
        tmp_path / "service_activity_power.json",
        {
            "model": "decoder_attention_decode_score_multivalue_service_activity_power_v1",
            "decision": "activity_backed_service_power_measured",
            "promotion_gate_pass": True,
            "precision_status": "unchanged_integer_contract_from_merged_cluster_equivalence_and_integrated_service",
            "selection_contract": {
                "case_id": "c1_p128_b4_rr",
                "cluster_count": 1,
                "required_flow_variant": "decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
                "clock_period_ns": 10.0,
                "status": "exactly_one_status_ok_timing_feasible_row_required",
            },
            "best_candidate_id": "multivalue_service_activity_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
            "best": {
                "candidate_id": "multivalue_service_activity_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
                "flow_variant": "decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
                "status": "activity_backed",
                "promotion_gate_pass": True,
                "ppa_metric": {
                    "design": "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr",
                    "platform": "nangate45",
                    "param_hash": "p1",
                    "config_hash": "cfg1",
                    "tag": "die3000",
                    "status": "ok",
                    "critical_path_ns": "9.2",
                    "instance_area_um2": "3000000",
                    "params_json": json.dumps(
                        {
                            "CLOCK_PERIOD": 10,
                            "FLOW_VARIANT": "decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
                        }
                    ),
                },
                "component_service_window_energy": {
                    "label": "component_service_window_energy",
                    "is_total_token_energy": False,
                    "cycle_count": 160,
                    "duration_s": 1.6e-6,
                    "energy_j": {
                        "dynamic": 4.8e-7,
                        "leakage": 8.0e-8,
                        "dynamic_plus_leakage": 5.6e-7,
                    },
                    **({"result_semantics": _result_semantics(result_mode)} if result_mode is not None else {}),
                },
                "authoritative_composed_c1_total_ppa": {
                    "critical_path_ns": 9.2,
                    "instance_area_um2": 3_000_000,
                    "die_area": 9_000_000,
                    "total_power_mw": 12.75,
                },
                "authoritative_composed_total_ppa": {
                    "critical_path_ns": 9.2,
                    "instance_area_um2": 3_000_000,
                    "die_area": 9_000_000,
                    "total_power_mw": 12.75,
                },
            },
            "dependency_contract": {
                "cluster_equivalence": {
                    "equivalence_pass": True,
                    "decision": "decode_score_multivalue_cluster_equivalence_pass",
                    "score_tensor_hash": "score-hash",
                    "final_tensor_hash": "final-hash",
                },
                "integrated_service_c1": {
                    "case_id": "c1_p128_b4_rr",
                    "config": {
                        "cluster_count": 1,
                        "packet_w": 128,
                        "banks": 4,
                        "req_queue_depth": 4,
                        "resp_queue_depth": 4,
                        "bank_queue_depth": 4,
                        "read_latency": 2,
                        "arb_mode": "round_robin",
                        "locality_burst_max": 2,
                    },
                    "workload_contract": _workload_contract(),
                    "decision": "pass",
                    "exact_match": True,
                    "no_protocol_errors": True,
                    "no_drop_duplicate_deadlock_timeout": True,
                    "cycle_bound_ok": True,
                    "hashes": {
                        "score_hash": "integrated-c1-score-hash",
                        "final_hash": "integrated-c1-final-hash",
                        "request_hash": "request-hash",
                        "wide_response_matrix_hash": "wide-hash",
                    },
                },
            },
            "activity_contract": {
                "clock_period_ns": 10.0,
                "cycle_count": 160,
                "workload_contract": _workload_contract(),
                **({"result_semantics": _result_semantics(result_mode)} if result_mode is not None else {}),
            },
            "macro_manifest_contract": {
                "counts": {"fakeram45_2048x39": 56, "fakeram45_64x32": 64},
            },
            "macro_activity_contract": {
                "profile": "multivalue_service_c1_v1",
                "total_assignment_count": 9704,
                "macro_classes": {
                    "fakeram45_2048x39": {
                        "instance_scope_prefix": "score_bank",
                        "instance_count": 56,
                        "pins_per_instance": 91,
                        "assignment_count": 5096,
                    },
                    "fakeram45_64x32": {
                        "instance_scope_prefix": "gen_value_macro_backend",
                        "instance_count": 64,
                        "pins_per_instance": 72,
                        "assignment_count": 4608,
                    },
                },
            },
            "bank3_dynamic_inactivity": {
                "inactive_banks": [3],
                "statement": (
                    "No artificial activity was injected. Bank3 may remain dynamically inactive in this exact c1 "
                    "workload; it is not required to toggle, while leakage remains part of routed power."
                ),
            },
        },
    )


def _service_activity_power_c2(tmp_path: Path, *, result_mode: str | None = "exact_partial") -> Path:
    return _write(
        tmp_path / "service_activity_power_c2.json",
        {
            "model": "decoder_attention_decode_score_multivalue_service_activity_power_v1",
            "decision": "activity_backed_service_power_measured",
            "promotion_gate_pass": True,
            "precision_status": "unchanged_integer_contract_from_merged_cluster_equivalence_and_integrated_service",
            "selection_contract": {
                "case_id": "c2_p128_b4_rr",
                "cluster_count": 2,
                "required_flow_variant": "decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                "clock_period_ns": 10.0,
                "status": "exactly_one_status_ok_timing_feasible_row_required",
            },
            "best_candidate_id": "multivalue_service_activity_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
            "best": {
                "candidate_id": "multivalue_service_activity_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                "flow_variant": "decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                "status": "activity_backed",
                "promotion_gate_pass": True,
                "ppa_metric": {
                    "design": "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
                    "platform": "nangate45",
                    "param_hash": "p2",
                    "config_hash": "cfg2",
                    "tag": "die3700",
                    "status": "ok",
                    "critical_path_ns": "9.7",
                    "instance_area_um2": "4500000",
                    "params_json": json.dumps(
                        {
                            "CLOCK_PERIOD": 10,
                            "FLOW_VARIANT": "decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                        }
                    ),
                },
                "component_service_window_energy": {
                    "label": "component_service_window_energy",
                    "is_total_token_energy": False,
                    "cycle_count": 8863,
                    "duration_s": 8.863e-5,
                    "energy_j": {
                        "dynamic": 1.0e-6,
                        "leakage": 2.0e-7,
                        "dynamic_plus_leakage": 1.2e-6,
                    },
                    **({"result_semantics": _result_semantics(result_mode)} if result_mode is not None else {}),
                },
                "authoritative_composed_c2_total_ppa": {
                    "critical_path_ns": 9.7,
                    "instance_area_um2": 4_500_000,
                    "die_area": 13_690_000,
                    "total_power_mw": 18.1,
                },
                "authoritative_composed_total_ppa": {
                    "critical_path_ns": 9.7,
                    "instance_area_um2": 4_500_000,
                    "die_area": 13_690_000,
                    "total_power_mw": 18.1,
                },
            },
            "dependency_contract": {
                "cluster_equivalence": {
                    "equivalence_pass": True,
                    "decision": "decode_score_multivalue_cluster_equivalence_pass",
                    "score_tensor_hash": "score-hash",
                    "final_tensor_hash": "final-hash",
                },
                "integrated_service_c2": {
                    "case_id": "c2_p128_b4_rr",
                    "config": {
                        "cluster_count": 2,
                        "packet_w": 128,
                        "banks": 4,
                        "req_queue_depth": 4,
                        "resp_queue_depth": 4,
                        "bank_queue_depth": 4,
                        "read_latency": 2,
                        "arb_mode": "round_robin",
                        "locality_burst_max": 2,
                    },
                    "workload_contract": _workload_contract(),
                    "decision": "pass",
                    "exact_match": True,
                    "no_protocol_errors": True,
                    "no_drop_duplicate_deadlock_timeout": True,
                    "cycle_bound_ok": True,
                    "hashes": {
                        "score_hash": "integrated-c2-score-hash",
                        "final_hash": "integrated-c2-final-hash",
                        "request_hash": "integrated-c2-request-hash",
                        "wide_response_matrix_hash": "integrated-c2-wide-hash",
                    },
                },
            },
            "activity_contract": {
                "clock_period_ns": 10.0,
                "cycle_count": 8863,
                "workload_contract": _workload_contract(),
                **({"result_semantics": _result_semantics(result_mode)} if result_mode is not None else {}),
            },
            "macro_manifest_contract": {
                "counts": {"fakeram45_2048x39": 112, "fakeram45_64x32": 64},
            },
            "macro_activity_contract": {
                "profile": "multivalue_service_c2_v1",
                "total_assignment_count": 14800,
                "macro_classes": {
                    "fakeram45_2048x39": {
                        "instance_scope_prefix": "score_bank",
                        "instance_count": 112,
                        "pins_per_instance": 91,
                        "assignment_count": 10192,
                    },
                    "fakeram45_64x32": {
                        "instance_scope_prefix": "gen_value_macro_backend",
                        "instance_count": 64,
                        "pins_per_instance": 72,
                        "assignment_count": 4608,
                    },
                },
            },
            "bank3_dynamic_inactivity": {
                "inactive_banks": [3],
                "statement": (
                    "No artificial activity was injected. Banks [3] may remain dynamically inactive in this exact "
                    "c2_p128_b4_rr workload; they are not required to toggle, while leakage remains part of routed power."
                ),
            },
        },
    )


def _online_exact_measured_reducer(tmp_path: Path) -> Path:
    return _write(
        tmp_path / "online_exact_measured_reducer.json",
        {
            "model": "llm_decoder_attention_score32_local_reducer_measured_recost_v1",
            "decision": "score32_local_reducer_measured_bounded_recost_recorded",
            "summary": {
                "single_clock_strict_latency_upper_bound_us": 172387.653024,
                "single_clock_strict_throughput_lower_bound_per_s": 5.800879485614,
                "dual_clock_strict_latency_upper_bound_us": 50588.450822,
                "dual_clock_strict_throughput_lower_bound_per_s": 19.767357642925,
            },
            "best_requested": {
                "replica_recost_clock_ns": 48.6509,
                "replica_recost_clock_origin": "inherited_single_clock_composed_compute_bound",
                "replica_recost_compute_power_mw": 25979.6,
                "replica_recost_logic_area_required_um2": 297277823.9308,
                "measured_shared_sram_used_area_um2": 50000000.0,
                "measured_tile_local_sram_area_um2": 30000000.0,
                "local_reducer_measured_recost_replaces_unresolved_local_reducer_timing": True,
            },
            "routed_component_ppa": {
                "macro_only_sum_scaled_16_clusters": {
                    "die_area_mm2": 92.3472,
                    "total_power_mw": 203.52,
                },
                "synthesis_area_lower_bound_scaled_16_clusters": {
                    "total_hierarchy_area_mm2": 52.753805,
                },
            },
            "remaining_abstractions": [
                "No total-token energy is claimed in this online-exact measured-reducer baseline.",
            ],
        },
    )


def test_build_report_success_recomputes_latency_area_and_component_energy(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_json=service,
    )

    assert payload["decision"] == "strict_c1_measured_service_anchor_promoted_c2plus_blocked"
    assert payload["inputs"]["source_schedule_json"].endswith("source_schedule.json")
    assert payload["schedule_contract"]["workload_contract"] == _workload_contract()
    assert len(payload["promoted_rows"]) == 1
    row = payload["best_measured_anchor"]
    assert row["cluster_count"] == 1
    assert row["clock_ns"] == 10.0
    assert row["dense_qkv_tile_count"] == 4
    assert row["qkv_cycles"] == 512
    assert row["attention_cycles"] == 12800
    assert row["layer_cycles"] == 13324
    assert row["total_cycles"] == 426368
    assert row["latency_us"] == pytest.approx(4263.68)
    assert row["logic_area_mm2"] == pytest.approx(12.0)
    assert row["embodied_logic_plus_existing_shared_tile_sram_area_mm2"] == pytest.approx(15.0)
    assert row["compute_budget_slack_mm2"] == pytest.approx(0.0)
    assert row["prior_cluster_area_mm2"] == pytest.approx(2.0)
    assert row["authoritative_composed_service_area_mm2"] == pytest.approx(3.0)
    assert "16KiB service value store" in row["area_replacement_provenance"]
    assert row["service_component_dynamic_energy_mj_per_token"] == pytest.approx(2684.68224)
    assert row["service_component_leakage_energy_mj_per_token"] == pytest.approx(0.2048)
    assert row["service_component_energy_mj_per_token"] == pytest.approx(2684.88704)
    assert row["direct_total_token_energy"] is False
    assert row["authoritative_composed_service_total_power_mw"] == pytest.approx(12.75)
    assert row["service_window_average_dynamic_plus_leakage_power_mw"] == pytest.approx(350.0)
    assert row["full_measured_window_count"] == 5462
    assert row["full_measured_window_count_exact"] == 5461
    assert row["final_partial_tokens"] == 8
    assert row["final_partial_window_conservatively_charged_as_full_measured_window"] is True
    comparison = row["comparison_to_online_exact_measured_reducer"]
    assert comparison["full_token_latency_directly_comparable"] is True
    assert comparison["full_token_throughput_directly_comparable"] is True
    assert comparison["energy_directly_comparable"] is False
    assert comparison["latency_ratio_vs_online_exact_single_clock_strict_upper_bound"] == pytest.approx(
        4263.68 / 172387.653024
    )
    assert comparison["latency_ratio_vs_online_exact_dual_clock_strict_upper_bound"] == pytest.approx(
        4263.68 / 50588.450822
    )
    assert comparison["service_total_power_ratio_vs_online_exact_macro_only_power_scaled_16_clusters"] == pytest.approx(
        12.75 / 203.52
    )
    baseline = payload["online_exact_measured_reducer_baseline"]
    assert baseline["replica_recost_embodied_logic_plus_existing_shared_tile_sram_area_mm2"] == pytest.approx(
        377.277823931
    )
    assert payload["online_exact_measured_reducer_comparison"]["dependency_job_sequence"] == [
        "c1 PNR",
        "c1 activity power",
        "measured frontier",
    ]
    assert (
        payload["selected_service_activity_candidate"]["integrated_service_hashes"]["score_hash"]
        == "integrated-c1-score-hash"
    )
    assert (
        payload["selected_service_activity_candidate"]["activity_workload_contract"]
        == _workload_contract()
    )


def test_build_report_prevents_old_cluster_and_service_area_double_count(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_json=service,
    )

    row = payload["best_measured_anchor"]
    assert row["dense_qkv_tile_count"] == 4
    assert row["logic_area_mm2"] == pytest.approx(12.0)
    assert row["area_replacement_delta_mm2"] == pytest.approx(1.0)


def test_build_report_accepts_distinct_integrated_hash_domain(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_json=service,
    )

    assert payload["precision"]["score_tensor_hash"] == "score-hash"
    assert (
        payload["selected_service_activity_candidate"]["integrated_service_hashes"]["score_hash"]
        == "integrated-c1-score-hash"
    )
    assert (
        payload["selected_service_activity_candidate"]["integrated_service_hashes"]["final_hash"]
        == "integrated-c1-final-hash"
    )


def test_build_report_rejects_normalized_service_result_semantics_for_frontier_scaling(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path, result_mode="normalized")
    online_exact = _online_exact_measured_reducer(tmp_path)

    with pytest.raises(ValueError, match="explicit exact_partial/composable result_semantics"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_rejects_legacy_missing_service_result_semantics_for_frontier_scaling(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path, result_mode=None)
    online_exact = _online_exact_measured_reducer(tmp_path)

    with pytest.raises(ValueError, match="result_semantics missing"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_rejects_cycle_mismatch(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)
    payload = json.loads(service.read_text(encoding="utf-8"))
    payload["activity_contract"]["cycle_count"] = 161
    payload["best"]["component_service_window_energy"]["cycle_count"] = 161
    payload["best"]["component_service_window_energy"]["duration_s"] = 1.61e-6
    service.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="microkernel cycle_count"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_rejects_structural_macro_gate_failure(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)
    payload = json.loads(service.read_text(encoding="utf-8"))
    payload["macro_activity_contract"]["macro_classes"]["fakeram45_64x32"]["assignment_count"] = 4607
    service.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="assignment_count mismatch"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_rejects_precision_gate_mismatch(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)
    payload = json.loads(service.read_text(encoding="utf-8"))
    payload["dependency_contract"]["cluster_equivalence"]["final_tensor_hash"] = "wrong-hash"
    service.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="final_tensor_hash mismatch"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_rejects_workload_contract_schema_drift(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)
    payload = json.loads(service.read_text(encoding="utf-8"))
    payload["activity_contract"]["workload_contract"]["active_context_tokens"] = 25
    service.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="workload_contract"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_uses_24_token_measured_window_ceil_and_partial_charge(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path, sequence_length=131000)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_json=service,
    )

    row = payload["best_measured_anchor"]
    assert row["full_measured_window_count"] == 5459
    assert row["full_measured_window_count_exact"] == 5458
    assert row["final_partial_tokens"] == 8
    assert row["final_partial_window_conservatively_charged_as_full_measured_window"] is True
    assert row["service_component_dynamic_energy_mj_per_token"] == pytest.approx(2683.20768)


def test_build_report_rejects_recomputed_infeasible_c1(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    prior_payload = json.loads(prior.read_text(encoding="utf-8"))
    linked_prior = Path(prior_payload["inputs"]["prior_frontier_json"])
    linked_payload = json.loads(linked_prior.read_text(encoding="utf-8"))
    source = Path(linked_payload["inputs"]["source_schedule_json"])
    source_payload = json.loads(source.read_text(encoding="utf-8"))
    source_payload["source_schedule"]["compute_budget_um2"] = 3_500_000
    source.write_text(json.dumps(source_payload), encoding="utf-8")
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    with pytest.raises(ValueError, match="not feasible for promotion"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_json=service,
        )


def test_build_report_keeps_c2_blocked_unpromoted(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service = _service_activity_power(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_json=service,
    )

    assert len(payload["rows"]) == 2
    blocked = payload["blocked_rows"]
    assert len(blocked) == 1
    assert blocked[0]["cluster_count"] == 2
    assert blocked[0]["promoted"] is False
    assert blocked[0]["rankable_as_measured"] is False
    assert "pending_equivalent_composed_physical_activity_evidence" in blocked[0]["status"]
    assert "best_throughput_candidate" not in payload
    assert "pareto_rows" not in payload


def test_build_report_promotes_c2_with_whole_service_window_accounting(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service_c1 = _service_activity_power(tmp_path)
    service_c2 = _service_activity_power_c2(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_jsons=[service_c1, service_c2],
    )

    assert payload["decision"] == "strict_c1_c2_measured_service_anchors_promoted_c3plus_blocked"
    assert len(payload["promoted_rows"]) == 2
    assert payload["best_throughput_candidate"]["cluster_count"] == 2
    assert {row["cluster_count"] for row in payload["pareto_rows"]} == {1, 2}
    c2_row = next(row for row in payload["promoted_rows"] if row["cluster_count"] == 2)
    assert c2_row["service_calibration_case_id"] == "c2_p128_b4_rr"
    assert c2_row["service_activity_microkernel_cycle_count"] == 8863
    assert c2_row["service_window_energy_accounting"] == (
        "whole_measured_service_window_scaled_by_measured_windows_and_service_waves"
    )
    assert c2_row["full_context_service_wave_count"] == 16 * 32
    assert c2_row["service_component_dynamic_energy_mj_per_token"] == pytest.approx(2796.544)
    assert c2_row["service_component_leakage_energy_mj_per_token"] == pytest.approx(0.00508360600248223)
    assert c2_row["service_component_energy_mj_per_token"] == pytest.approx(2796.5490836060025)
    assert "full_context_dynamic_energy_j_per_head_command" not in c2_row
    assert "full_context_leakage_energy_j_per_head_command" not in c2_row
    c1_row = next(row for row in payload["promoted_rows"] if row["cluster_count"] == 1)
    assert "full_context_dynamic_energy_j_per_head_command" in c1_row
    assert "full_context_leakage_energy_j_per_head_command" in c1_row


def test_build_report_c2_regression_guard_rejects_head_count_double_count(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service_c1 = _service_activity_power(tmp_path)
    service_c2 = _service_activity_power_c2(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)

    payload = build_report(
        prior_cluster_frontier_json=prior,
        online_exact_measured_reducer_json=online_exact,
        service_activity_power_jsons=[service_c1, service_c2],
    )

    c2_row = next(row for row in payload["promoted_rows"] if row["cluster_count"] == 2)
    wrong_dynamic_mj = 1.0e-6 * math.ceil(131072 / 24) * 32 * 32 * 1.0e3
    assert c2_row["service_component_dynamic_energy_mj_per_token"] != pytest.approx(wrong_dynamic_mj)


def test_build_report_rejects_c2_cycle_mismatch(tmp_path: Path) -> None:
    prior = _prior_frontier(tmp_path)
    service_c1 = _service_activity_power(tmp_path)
    service_c2 = _service_activity_power_c2(tmp_path)
    online_exact = _online_exact_measured_reducer(tmp_path)
    payload = json.loads(service_c2.read_text(encoding="utf-8"))
    payload["activity_contract"]["cycle_count"] = 8864
    payload["best"]["component_service_window_energy"]["cycle_count"] = 8864
    payload["best"]["component_service_window_energy"]["duration_s"] = 8.864e-5
    service_c2.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="service activity cycle_count"):
        build_report(
            prior_cluster_frontier_json=prior,
            online_exact_measured_reducer_json=online_exact,
            service_activity_power_jsons=[service_c1, service_c2],
        )

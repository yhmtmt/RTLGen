#!/usr/bin/env python3
"""Compose strict measured-service frontier anchors for Llama7B decode."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVALUATOR_LOCAL_PATH_PLACEHOLDER = "<evaluator-local-path>"

_MODEL = "decoder_attention_decode_score_multivalue_service_measured_frontier_llama7b_v1"
_EXPECTED_PRIOR_MODEL = "decoder_attention_decode_score_multivalue_cluster_frontier_llama7b_v1"
_EXPECTED_PRIOR_DECISION = "shared_score_multivalue_cluster_measured_component_frontier_promoted"
_EXPECTED_PRIOR_PROMOTION = "component_frontier_promoted_full_architecture_promotion_blocked"
_EXPECTED_PRIOR_ITEM_ID = "l2_decoder_attention_decode_score_multivalue_cluster_frontier_llama7b_v1_r1"
_EXPECTED_PRIOR_PRECISION_STATUS = "unchanged_integer_contract_from_merged_multivalue_equivalence"
_EXPECTED_PRIOR_PRECISION_DECISION = "decode_score_multivalue_cluster_equivalence_pass"

_EXPECTED_SERVICE_MODEL = "decoder_attention_decode_score_multivalue_service_activity_power_v1"
_EXPECTED_SERVICE_DECISION = "activity_backed_service_power_measured"
_EXPECTED_SERVICE_PRECISION_STATUS = (
    "unchanged_integer_contract_from_merged_cluster_equivalence_and_integrated_service"
)
_EXPECTED_SERVICE_PLATFORM = "nangate45"
_EXPECTED_HIDDEN = 4096
_EXPECTED_HEADS = 32
_EXPECTED_KV_HEADS = 4
_EXPECTED_LAYERS = 32
_EXPECTED_SERVICE_CLOCK_NS = 10.0
_EXPECTED_ONLINE_EXACT_MODEL = "llm_decoder_attention_score32_local_reducer_measured_recost_v1"
_EXPECTED_ONLINE_EXACT_DECISION = "score32_local_reducer_measured_bounded_recost_recorded"
_EXPECTED_WORKLOAD_CONTRACT = {
    "command_block_count": 3,
    "context_tokens_per_block": 8,
    "active_context_tokens": 24,
    "max_blocks": 16,
    "max_context_capacity_tokens": 128,
    "value_dim": 128,
}
_SERVICE_CASES = {
    "c1_p128_b4_rr": {
        "cluster_count": 1,
        "flow_variant": "decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1",
        "design": "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr",
        "macro_counts": {"fakeram45_2048x39": 56, "fakeram45_64x32": 64},
        "dependency_key": "integrated_service_c1",
        "authoritative_key": "authoritative_composed_c1_total_ppa",
    },
    "c2_p128_b4_rr": {
        "cluster_count": 2,
        "flow_variant": "decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
        "design": "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
        "macro_counts": {"fakeram45_2048x39": 112, "fakeram45_64x32": 64},
        "dependency_key": "integrated_service_c2",
        "authoritative_key": "authoritative_composed_c2_total_ppa",
    },
}


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _portable_path(path: Path) -> str:
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return f"{_EVALUATOR_LOCAL_PATH_PLACEHOLDER}/{path.name}"


def _positive(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def _nonnegative(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0 or not numeric.is_integer():
        raise ValueError(f"{label} must be a positive integer")
    return int(numeric)


def _nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a nonnegative integer")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0 or not numeric.is_integer():
        raise ValueError(f"{label} must be a nonnegative integer")
    return int(numeric)


def _string(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _resolved_path(path_value: str, base_path: Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = base_path.parent / path
    return path.resolve()


def _extract_schedule(payload: JsonDict, label: str) -> JsonDict:
    schedule = payload.get("source_schedule")
    if isinstance(schedule, dict):
        return schedule
    if "hidden_size" in payload and "attention_heads" in payload and "sequence_length" in payload:
        return payload
    raise ValueError(f"{label} lacks source_schedule")


def _validated_workload_contract(payload: Any, label: str) -> JsonDict:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    validated: JsonDict = {}
    for key, expected in _EXPECTED_WORKLOAD_CONTRACT.items():
        value = _positive_int(payload.get(key), f"{label} {key}")
        if value != expected:
            raise ValueError(f"{label} {key} mismatch: expected {expected}, got {value}")
        validated[key] = value
    return validated


def _validated_result_semantics(payload: Any, label: str) -> JsonDict:
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be an object")
    result_mode = _string(payload.get("result_mode"), f"{label} result_mode")
    if result_mode not in {"normalized", "exact_partial"}:
        raise ValueError(f"{label} result_mode must be normalized or exact_partial")
    supports_sequence_window_composition = payload.get("supports_sequence_window_composition")
    if not isinstance(supports_sequence_window_composition, bool):
        raise ValueError(f"{label} supports_sequence_window_composition must be a boolean")
    if supports_sequence_window_composition != (result_mode == "exact_partial"):
        raise ValueError(f"{label} supports_sequence_window_composition mismatches result_mode")
    composition_scope = _string(payload.get("composition_scope"), f"{label} composition_scope")
    expected_scope = (
        "exact_partial_across_sequence_windows_before_finalization"
        if result_mode == "exact_partial"
        else "normalized_final_output_not_sequence_window_composable"
    )
    if composition_scope != expected_scope:
        raise ValueError(f"{label} composition_scope mismatch")
    return {
        "result_mode": result_mode,
        "supports_sequence_window_composition": supports_sequence_window_composition,
        "composition_scope": composition_scope,
    }


def _source_schedule(frontier: JsonDict, frontier_path: Path) -> tuple[JsonDict, str]:
    visited = {frontier_path.resolve()}
    current_payload = frontier
    current_path = frontier_path.resolve()
    for _ in range(8):
        inputs = current_payload.get("inputs")
        if isinstance(inputs, dict):
            source_schedule_json = inputs.get("source_schedule_json")
            if isinstance(source_schedule_json, str) and source_schedule_json.strip():
                source_path = _resolved_path(source_schedule_json, current_path)
                return _extract_schedule(_load(source_path), "linked source_schedule_json"), _portable_path(source_path)
        schedule = current_payload.get("source_schedule")
        if isinstance(schedule, dict):
            return schedule, _portable_path(current_path)
        linked = inputs.get("prior_frontier_json") if isinstance(inputs, dict) else None
        if not isinstance(linked, str) or not linked.strip():
            raise ValueError("prior frontier lacks inputs.source_schedule_json and a recursive prior_frontier_json chain")
        current_path = _resolved_path(linked, current_path)
        if current_path in visited:
            raise ValueError("prior frontier source_schedule resolution encountered a cycle")
        visited.add(current_path)
        current_payload = _load(current_path)
    raise ValueError("prior frontier source_schedule resolution exceeded the maximum recursion depth")


def _validate_optional_item_id(payload: JsonDict, expected: str, label: str) -> None:
    for key in ("item_id", "report_item_id", "promotion_item_id"):
        value = payload.get(key)
        if value is None:
            continue
        if _string(value, f"{label} {key}") != expected:
            raise ValueError(f"{label} {key} mismatch: expected {expected}")
        break


def _service_case(case_id: str) -> JsonDict:
    contract = _SERVICE_CASES.get(str(case_id).strip())
    if contract is None:
        raise ValueError(f"unsupported measured-service case_id: {case_id}")
    return {"case_id": str(case_id).strip(), **dict(contract)}


def _validated_online_exact_measured_reducer(payload: JsonDict) -> JsonDict:
    if _string(payload.get("model"), "online-exact measured-reducer model") != _EXPECTED_ONLINE_EXACT_MODEL:
        raise ValueError("online-exact measured-reducer report has an unexpected model")
    if _string(payload.get("decision"), "online-exact measured-reducer decision") != _EXPECTED_ONLINE_EXACT_DECISION:
        raise ValueError("online-exact measured-reducer report has an unexpected decision")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("online-exact measured-reducer report lacks summary")
    best_requested = payload.get("best_requested")
    if not isinstance(best_requested, dict):
        raise ValueError("online-exact measured-reducer report lacks best_requested")
    routed_component_ppa = payload.get("routed_component_ppa")
    if not isinstance(routed_component_ppa, dict):
        raise ValueError("online-exact measured-reducer report lacks routed_component_ppa")
    macro_only_scaled = routed_component_ppa.get("macro_only_sum_scaled_16_clusters")
    if not isinstance(macro_only_scaled, dict):
        raise ValueError("online-exact measured-reducer report lacks scaled macro-only PPA")
    synthesis_scaled = routed_component_ppa.get("synthesis_area_lower_bound_scaled_16_clusters")
    if not isinstance(synthesis_scaled, dict):
        raise ValueError("online-exact measured-reducer report lacks scaled synthesis lower bound")
    if best_requested.get("local_reducer_measured_recost_replaces_unresolved_local_reducer_timing") is not True:
        raise ValueError("online-exact measured-reducer report must replace unresolved local-reducer timing")
    embodied_area_um2 = (
        _positive(
            best_requested.get("replica_recost_logic_area_required_um2"),
            "online-exact replica_recost_logic_area_required_um2",
        )
        + _nonnegative(
            best_requested.get("measured_shared_sram_used_area_um2"),
            "online-exact measured_shared_sram_used_area_um2",
        )
        + _nonnegative(
            best_requested.get("measured_tile_local_sram_area_um2"),
            "online-exact measured_tile_local_sram_area_um2",
        )
    )
    return {
        "model": _EXPECTED_ONLINE_EXACT_MODEL,
        "decision": _EXPECTED_ONLINE_EXACT_DECISION,
        "single_clock_strict_latency_upper_bound_us": _positive(
            summary.get("single_clock_strict_latency_upper_bound_us"),
            "online-exact single_clock_strict_latency_upper_bound_us",
        ),
        "single_clock_strict_throughput_lower_bound_per_s": _positive(
            summary.get("single_clock_strict_throughput_lower_bound_per_s"),
            "online-exact single_clock_strict_throughput_lower_bound_per_s",
        ),
        "dual_clock_strict_latency_upper_bound_us": _positive(
            summary.get("dual_clock_strict_latency_upper_bound_us"),
            "online-exact dual_clock_strict_latency_upper_bound_us",
        ),
        "dual_clock_strict_throughput_lower_bound_per_s": _positive(
            summary.get("dual_clock_strict_throughput_lower_bound_per_s"),
            "online-exact dual_clock_strict_throughput_lower_bound_per_s",
        ),
        "replica_recost_clock_ns": _positive(
            best_requested.get("replica_recost_clock_ns"),
            "online-exact replica_recost_clock_ns",
        ),
        "replica_recost_clock_origin": _string(
            best_requested.get("replica_recost_clock_origin"),
            "online-exact replica_recost_clock_origin",
        ),
        "replica_recost_compute_power_mw": _positive(
            best_requested.get("replica_recost_compute_power_mw"),
            "online-exact replica_recost_compute_power_mw",
        ),
        "replica_recost_embodied_logic_plus_existing_shared_tile_sram_area_mm2": round(
            embodied_area_um2 / 1.0e6,
            9,
        ),
        "macro_only_area_mm2_scaled_16_clusters": _positive(
            macro_only_scaled.get("die_area_mm2"),
            "online-exact macro_only_area_mm2_scaled_16_clusters",
        ),
        "macro_only_power_mw_scaled_16_clusters": _positive(
            macro_only_scaled.get("total_power_mw"),
            "online-exact macro_only_power_mw_scaled_16_clusters",
        ),
        "synthesis_area_lower_bound_mm2_scaled_16_clusters": _positive(
            synthesis_scaled.get("total_hierarchy_area_mm2"),
            "online-exact synthesis_area_lower_bound_mm2_scaled_16_clusters",
        ),
        "remaining_abstractions": [
            _string(item, "online-exact remaining_abstractions item")
            for item in payload.get("remaining_abstractions", [])
        ],
    }


def _service_macro_profile(case_contract: JsonDict) -> str:
    return f"multivalue_service_{str(case_contract['case_id']).split('_', 1)[0]}_v1"


def _validated_prior_frontier(
    prior: JsonDict, prior_frontier_json: Path
) -> tuple[JsonDict, str, JsonDict, dict[int, JsonDict], list[JsonDict], JsonDict, JsonDict]:
    if _string(prior.get("model"), "prior frontier model") != _EXPECTED_PRIOR_MODEL:
        raise ValueError("prior frontier has an unexpected model")
    if _string(prior.get("decision"), "prior frontier decision") != _EXPECTED_PRIOR_DECISION:
        raise ValueError("prior frontier has an unexpected decision")
    if _string(prior.get("promotion_status"), "prior frontier promotion_status") != _EXPECTED_PRIOR_PROMOTION:
        raise ValueError("prior frontier has an unexpected promotion_status")
    _validate_optional_item_id(prior, _EXPECTED_PRIOR_ITEM_ID, "prior frontier")
    precision = prior.get("precision")
    if not isinstance(precision, dict):
        raise ValueError("prior frontier lacks precision evidence")
    if precision.get("equivalence_pass") is not True:
        raise ValueError("prior frontier precision equivalence did not pass")
    if _string(precision.get("status"), "prior frontier precision status") != _EXPECTED_PRIOR_PRECISION_STATUS:
        raise ValueError("prior frontier precision status mismatch")
    if _string(precision.get("decision"), "prior frontier precision decision") != _EXPECTED_PRIOR_PRECISION_DECISION:
        raise ValueError("prior frontier precision decision mismatch")
    if (
        _string(precision.get("quality_change"), "prior frontier quality_change")
        != "none_exact_integer_semantics_preserved"
    ):
        raise ValueError("prior frontier quality_change mismatch")
    schedule_contract = prior.get("schedule_contract")
    if not isinstance(schedule_contract, dict):
        raise ValueError("prior frontier lacks schedule_contract")
    if _positive_int(schedule_contract.get("hidden_size"), "prior hidden_size") != _EXPECTED_HIDDEN:
        raise ValueError("prior frontier hidden_size mismatch")
    if _positive_int(schedule_contract.get("attention_heads"), "prior attention_heads") != _EXPECTED_HEADS:
        raise ValueError("prior frontier attention_heads mismatch")
    if _positive_int(schedule_contract.get("kv_heads"), "prior kv_heads") != _EXPECTED_KV_HEADS:
        raise ValueError("prior frontier kv_heads mismatch")
    if _positive_int(schedule_contract.get("layers"), "prior layers") != _EXPECTED_LAYERS:
        raise ValueError("prior frontier layers mismatch")
    sequence_length = _positive_int(schedule_contract.get("sequence_length"), "prior sequence_length")
    if schedule_contract.get("sequence_sharding_supported") is not False:
        raise ValueError("prior frontier must keep sequence_sharding_supported=false")
    dense_qkv_tile = prior.get("dense_qkv_tile")
    if not isinstance(dense_qkv_tile, dict):
        raise ValueError("prior frontier lacks dense_qkv_tile evidence")
    _positive(dense_qkv_tile.get("area_um2"), "dense_qkv_tile area_um2")
    _positive(dense_qkv_tile.get("effective_macs_per_cycle"), "dense_qkv_tile effective_macs_per_cycle")
    calibration = prior.get("service_cycle_calibration")
    if not isinstance(calibration, dict):
        raise ValueError("prior frontier lacks service_cycle_calibration")
    probe_contract = calibration.get("probe_contract")
    if not isinstance(probe_contract, dict):
        raise ValueError("prior frontier lacks service probe_contract")
    workload_contract = _validated_workload_contract(probe_contract, "prior frontier probe_contract")
    rows = [row for row in prior.get("rows", []) if isinstance(row, dict)]
    if not rows:
        raise ValueError("prior frontier has no rows")
    prior_rows_by_cluster: dict[int, JsonDict] = {}
    for row in rows:
        cluster_count = _positive_int(row.get("cluster_count"), "prior frontier cluster_count")
        if cluster_count in prior_rows_by_cluster:
            raise ValueError(f"prior frontier has multiple c{cluster_count} rows")
        prior_rows_by_cluster[cluster_count] = row
        expected_case_id = f"c{cluster_count}_p128_b4_rr"
        if _string(
            row.get("service_calibration_case_id"),
            f"prior c{cluster_count} service_calibration_case_id",
        ) != expected_case_id:
            raise ValueError(f"prior frontier c{cluster_count} service_calibration_case_id mismatch")
        _positive_int(
            row.get("service_calibration_microkernel_integrated_completion_cycle"),
            f"prior c{cluster_count} service_calibration_microkernel_integrated_completion_cycle",
        )
        if _positive_int(
            row.get("head_commands_per_layer"),
            f"prior c{cluster_count} head_commands_per_layer",
        ) != _EXPECTED_HEADS:
            raise ValueError(f"prior frontier c{cluster_count} head_commands_per_layer mismatch")
        _positive_int(
            row.get("cluster_waves_per_layer"),
            f"prior c{cluster_count} cluster_waves_per_layer",
        )
        _positive_int(
            row.get("service_no_stall_full_context_cycles_per_wave"),
            f"prior c{cluster_count} service_no_stall_full_context_cycles_per_wave",
        )
        _positive_int(
            row.get("service_calibrated_full_context_cycles_per_wave"),
            f"prior c{cluster_count} service_calibrated_full_context_cycles_per_wave",
        )
        _nonnegative_int(row.get("fixed_cycles"), f"prior c{cluster_count} fixed_cycles")
        _positive(row.get("clock_ns"), f"prior c{cluster_count} clock_ns")
    if 1 not in prior_rows_by_cluster:
        raise ValueError("prior frontier must contain exactly one c1 row")
    c1_row = prior_rows_by_cluster[1]
    if _positive_int(c1_row.get("cluster_waves_per_layer"), "prior c1 cluster_waves_per_layer") != _EXPECTED_HEADS:
        raise ValueError("prior frontier c1 cluster_waves_per_layer mismatch")
    schedule, schedule_source = _source_schedule(prior, prior_frontier_json)
    if _positive_int(schedule.get("hidden_size"), "resolved schedule hidden_size") != _positive_int(
        schedule_contract.get("hidden_size"), "prior contract hidden_size"
    ):
        raise ValueError("resolved schedule hidden_size mismatch vs prior schedule_contract")
    if _positive_int(schedule.get("attention_heads"), "resolved schedule attention_heads") != _positive_int(
        schedule_contract.get("attention_heads"), "prior contract attention_heads"
    ):
        raise ValueError("resolved schedule attention_heads mismatch vs prior schedule_contract")
    if _positive_int(schedule.get("kv_heads"), "resolved schedule kv_heads") != _positive_int(
        schedule_contract.get("kv_heads"), "prior contract kv_heads"
    ):
        raise ValueError("resolved schedule kv_heads mismatch vs prior schedule_contract")
    if _positive_int(schedule.get("layers"), "resolved schedule layers") != _positive_int(
        schedule_contract.get("layers"), "prior contract layers"
    ):
        raise ValueError("resolved schedule layers mismatch vs prior schedule_contract")
    if _positive_int(schedule.get("sequence_length"), "resolved schedule sequence_length") != sequence_length:
        raise ValueError("resolved schedule sequence_length mismatch vs prior schedule_contract")
    return (
        schedule,
        schedule_source,
        dense_qkv_tile,
        prior_rows_by_cluster,
        sorted(rows, key=lambda row: _positive_int(row.get("cluster_count"), "prior row cluster_count")),
        precision,
        workload_contract,
    )


def _validated_service_activity(
    service_report: JsonDict,
    prior_precision: JsonDict,
    prior_workload_contract: JsonDict,
) -> JsonDict:
    if _string(service_report.get("model"), "service activity-power model") != _EXPECTED_SERVICE_MODEL:
        raise ValueError("service activity-power report has an unexpected model")
    if _string(service_report.get("decision"), "service activity-power decision") != _EXPECTED_SERVICE_DECISION:
        raise ValueError("service activity-power report has an unexpected decision")
    if service_report.get("promotion_gate_pass") is not True:
        raise ValueError("service activity-power promotion gate did not pass")
    if (
        _string(service_report.get("precision_status"), "service activity-power precision_status")
        != _EXPECTED_SERVICE_PRECISION_STATUS
    ):
        raise ValueError("service activity-power precision_status mismatch")
    selection_contract = service_report.get("selection_contract")
    if not isinstance(selection_contract, dict):
        raise ValueError("service activity-power report lacks selection_contract")
    case_id = _string(selection_contract.get("case_id"), "service selection_contract case_id")
    case_contract = _service_case(case_id)
    if _positive_int(
        selection_contract.get("cluster_count"),
        "service selection_contract cluster_count",
    ) != int(case_contract["cluster_count"]):
        raise ValueError("service selection_contract cluster_count mismatch")
    best = service_report.get("best")
    if not isinstance(best, dict):
        raise ValueError("service activity-power report lacks best")
    if _string(service_report.get("best_candidate_id"), "service best_candidate_id") != _string(
        best.get("candidate_id"), "service best candidate_id"
    ):
        raise ValueError("service best_candidate_id mismatch")
    if _string(best.get("status"), "service best status") != "activity_backed":
        raise ValueError("service best is not activity_backed")
    if best.get("promotion_gate_pass") is not True:
        raise ValueError("service best promotion_gate_pass failed")
    if _string(best.get("flow_variant"), "service best flow_variant") != case_contract["flow_variant"]:
        raise ValueError("service best flow_variant mismatch")
    metric = best.get("ppa_metric")
    if not isinstance(metric, dict):
        raise ValueError("service best lacks ppa_metric")
    if _string(metric.get("design"), "service best design") != case_contract["design"]:
        raise ValueError("service best design mismatch")
    if _string(metric.get("platform"), "service best platform") != _EXPECTED_SERVICE_PLATFORM:
        raise ValueError("service best platform mismatch")
    params_json = json.loads(_string(metric.get("params_json"), "service best params_json"))
    if not isinstance(params_json, dict):
        raise ValueError("service best params_json is not an object")
    if _string(params_json.get("FLOW_VARIANT"), "service best FLOW_VARIANT") != case_contract["flow_variant"]:
        raise ValueError("service best FLOW_VARIANT mismatch")
    if abs(_positive(params_json.get("CLOCK_PERIOD"), "service best CLOCK_PERIOD") - _EXPECTED_SERVICE_CLOCK_NS) > 1e-9:
        raise ValueError("service best CLOCK_PERIOD mismatch")
    if _positive(metric.get("critical_path_ns"), "service best critical_path_ns") > _EXPECTED_SERVICE_CLOCK_NS:
        raise ValueError("service best is not timing-feasible at 10 ns")
    authoritative = best.get("authoritative_composed_total_ppa")
    if not isinstance(authoritative, dict):
        authoritative = best.get(case_contract["authoritative_key"])
    if not isinstance(authoritative, dict):
        raise ValueError("service best lacks authoritative composed-service PPA")
    if _positive(authoritative.get("critical_path_ns"), "authoritative service critical_path_ns") > _EXPECTED_SERVICE_CLOCK_NS:
        raise ValueError("authoritative composed-service instance is not timing-feasible at 10 ns")
    if not math.isclose(
        _positive(authoritative.get("instance_area_um2"), "authoritative service instance_area_um2"),
        _positive(metric.get("instance_area_um2"), "service best instance_area_um2"),
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("authoritative composed-service instance area mismatches service best ppa_metric")
    if not math.isclose(
        _positive(authoritative.get("critical_path_ns"), "authoritative service critical_path_ns"),
        _positive(metric.get("critical_path_ns"), "service best critical_path_ns"),
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("authoritative composed-service timing mismatches service best ppa_metric")
    counts = service_report.get("macro_manifest_contract")
    if not isinstance(counts, dict) or not isinstance(counts.get("counts"), dict):
        raise ValueError("service report lacks macro_manifest_contract counts")
    if counts["counts"] != case_contract["macro_counts"]:
        raise ValueError("service macro count contract mismatch")
    macro_activity_contract = service_report.get("macro_activity_contract")
    if not isinstance(macro_activity_contract, dict):
        raise ValueError("service report lacks macro_activity_contract")
    if _string(macro_activity_contract.get("profile"), "service macro_activity profile") != _service_macro_profile(
        case_contract
    ):
        raise ValueError("service macro_activity profile mismatch")
    macro_classes = macro_activity_contract.get("macro_classes")
    if not isinstance(macro_classes, dict):
        raise ValueError("service macro_activity_contract lacks macro_classes")
    if set(macro_classes) != set(case_contract["macro_counts"]):
        raise ValueError("service macro_activity_contract macro_classes mismatch")
    assignment_total = 0
    for macro_name, expected_count in case_contract["macro_counts"].items():
        payload = macro_classes.get(macro_name)
        if not isinstance(payload, dict):
            raise ValueError(f"service macro_activity_contract missing {macro_name}")
        instance_count = _positive_int(payload.get("instance_count"), f"{macro_name} instance_count")
        pins_per_instance = _positive_int(payload.get("pins_per_instance"), f"{macro_name} pins_per_instance")
        assignment_count = _positive_int(payload.get("assignment_count"), f"{macro_name} assignment_count")
        _string(payload.get("instance_scope_prefix"), f"{macro_name} instance_scope_prefix")
        if instance_count != expected_count:
            raise ValueError(f"service macro_activity_contract {macro_name} instance_count mismatch")
        if assignment_count != instance_count * pins_per_instance:
            raise ValueError(f"service macro_activity_contract {macro_name} assignment_count mismatch")
        assignment_total += assignment_count
    if _positive_int(
        macro_activity_contract.get("total_assignment_count"),
        "service macro_activity total_assignment_count",
    ) != assignment_total:
        raise ValueError("service macro_activity total_assignment_count mismatch")
    activity_contract = service_report.get("activity_contract")
    if not isinstance(activity_contract, dict):
        raise ValueError("service report lacks activity_contract")
    if abs(_positive(activity_contract.get("clock_period_ns"), "service activity_contract clock_period_ns") - _EXPECTED_SERVICE_CLOCK_NS) > 1e-9:
        raise ValueError("service activity clock_period_ns mismatch")
    if "result_semantics" not in activity_contract:
        raise ValueError(
            "service activity_contract result_semantics missing; legacy or normalized-only evidence cannot anchor measured-frontier scaling"
        )
    activity_result_semantics = _validated_result_semantics(
        activity_contract.get("result_semantics"),
        "service activity_contract result_semantics",
    )
    workload_contract = _validated_workload_contract(
        activity_contract.get("workload_contract"),
        "service activity_contract workload_contract",
    )
    if workload_contract != prior_workload_contract:
        raise ValueError("service activity_contract workload_contract mismatch vs prior probe_contract")
    bank3 = service_report.get("bank3_dynamic_inactivity")
    if not isinstance(bank3, dict):
        raise ValueError("service report lacks bank3_dynamic_inactivity")
    bank3_statement = _string(bank3.get("statement"), "service bank3 statement")
    if "No artificial activity was injected" not in bank3_statement or "not required to toggle" not in bank3_statement:
        raise ValueError("service report bank3 inactivity must be explicitly unforced")
    if case_id == "c1_p128_b4_rr" and bank3.get("inactive_banks") != [3]:
        raise ValueError("service report must keep bank3 inactive for c1")
    service_window = best.get("component_service_window_energy")
    if not isinstance(service_window, dict):
        raise ValueError("service best lacks component_service_window_energy")
    if _string(service_window.get("label"), "service component_service_window_energy label") != "component_service_window_energy":
        raise ValueError("service component_service_window_energy label mismatch")
    if service_window.get("is_total_token_energy") is not False:
        raise ValueError("service component_service_window_energy must not be total-token energy")
    if "result_semantics" not in service_window:
        raise ValueError(
            "service component_service_window_energy result_semantics missing; legacy or normalized-only evidence cannot anchor measured-frontier scaling"
        )
    service_window_result_semantics = _validated_result_semantics(
        service_window.get("result_semantics"),
        "service component_service_window_energy result_semantics",
    )
    if service_window_result_semantics != activity_result_semantics:
        raise ValueError("service result_semantics mismatch between activity_contract and component_service_window_energy")
    if activity_result_semantics["result_mode"] != "exact_partial":
        raise ValueError(
            "service measured-frontier promotion requires explicit exact_partial/composable result_semantics; normalized output evidence remains component-only"
        )
    service_cycle_count = _positive_int(service_window.get("cycle_count"), "service window cycle_count")
    if service_cycle_count != _positive_int(activity_contract.get("cycle_count"), "service activity cycle_count"):
        raise ValueError("service window cycle_count does not match activity_contract cycle_count")
    expected_duration_s = service_cycle_count * _EXPECTED_SERVICE_CLOCK_NS * 1.0e-9
    if not math.isclose(
        _positive(service_window.get("duration_s"), "service window duration_s"),
        expected_duration_s,
        rel_tol=0.0,
        abs_tol=1e-18,
    ):
        raise ValueError("service window duration_s mismatch")
    energy_j = service_window.get("energy_j")
    if not isinstance(energy_j, dict):
        raise ValueError("service window lacks energy_j")
    _positive(energy_j.get("dynamic"), "service window dynamic energy")
    _positive(energy_j.get("leakage"), "service window leakage energy")
    if not math.isclose(
        _positive(energy_j.get("dynamic"), "service window dynamic energy")
        + _positive(energy_j.get("leakage"), "service window leakage energy"),
        _positive(energy_j.get("dynamic_plus_leakage"), "service window total energy"),
        rel_tol=0.0,
        abs_tol=1e-18,
    ):
        raise ValueError("service window total energy does not match dynamic+leakage")
    dependency_contract = service_report.get("dependency_contract")
    if not isinstance(dependency_contract, dict):
        raise ValueError("service report lacks dependency_contract")
    cluster_equivalence = dependency_contract.get("cluster_equivalence")
    if not isinstance(cluster_equivalence, dict):
        raise ValueError("service dependency_contract lacks cluster_equivalence")
    if cluster_equivalence.get("equivalence_pass") is not True:
        raise ValueError("service cluster equivalence did not pass")
    if _string(cluster_equivalence.get("decision"), "service cluster equivalence decision") != _EXPECTED_PRIOR_PRECISION_DECISION:
        raise ValueError("service cluster equivalence decision mismatch")
    for field in ("score_tensor_hash", "final_tensor_hash"):
        if _string(cluster_equivalence.get(field), f"service cluster equivalence {field}") != _string(
            prior_precision.get(field), f"prior precision {field}"
        ):
            raise ValueError(f"service cluster equivalence {field} mismatch")
    integrated_service = dependency_contract.get(case_contract["dependency_key"])
    if not isinstance(integrated_service, dict):
        raise ValueError(f"service dependency_contract lacks {case_contract['dependency_key']}")
    if _string(integrated_service.get("case_id"), "service integrated_service case_id") != case_id:
        raise ValueError("service integrated_service case_id mismatch")
    if _string(integrated_service.get("decision"), "service integrated_service decision") != "pass":
        raise ValueError("service integrated_service decision mismatch")
    config = integrated_service.get("config")
    if not isinstance(config, dict):
        raise ValueError("service integrated_service config is missing")
    expected_config = {
        "cluster_count": int(case_contract["cluster_count"]),
        "packet_w": 128,
        "banks": 4,
        "req_queue_depth": 4,
        "resp_queue_depth": 4,
        "bank_queue_depth": 4,
        "read_latency": 2,
        "arb_mode": "round_robin",
        "locality_burst_max": 2,
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise ValueError(f"service integrated_service config mismatch for {key}")
    integrated_workload_contract = _validated_workload_contract(
        integrated_service.get("workload_contract"),
        "service integrated_service workload_contract",
    )
    if integrated_workload_contract != workload_contract:
        raise ValueError("service integrated_service workload_contract mismatch vs activity workload_contract")
    for key in ("exact_match", "no_protocol_errors", "no_drop_duplicate_deadlock_timeout", "cycle_bound_ok"):
        if integrated_service.get(key) is not True:
            raise ValueError(f"service integrated_service {key} gate failed")
    hashes = integrated_service.get("hashes")
    if not isinstance(hashes, dict):
        raise ValueError("service integrated_service lacks hashes")
    integrated_hashes = {
        "score_hash": _string(hashes.get("score_hash"), "service integrated_service score_hash"),
        "final_hash": _string(hashes.get("final_hash"), "service integrated_service final_hash"),
        "request_hash": _string(hashes.get("request_hash"), "service integrated_service request_hash"),
        "wide_response_matrix_hash": _string(
            hashes.get("wide_response_matrix_hash"),
            "service integrated_service wide_response_matrix_hash",
        ),
    }
    row = {
        "case_id": case_id,
        "cluster_count": int(case_contract["cluster_count"]),
        "best": best,
        "authoritative_service_ppa": authoritative,
        "service_window": service_window,
        "activity_contract": activity_contract,
        "workload_contract": workload_contract,
        "macro_activity_contract": macro_activity_contract,
        "integrated_hashes": integrated_hashes,
        "flow_variant": case_contract["flow_variant"],
        "design": case_contract["design"],
        "result_semantics": activity_result_semantics,
    }
    return row


def _recompute_dense_tiles(
    *,
    schedule: JsonDict,
    dense_qkv_tile: JsonDict,
    service_area_um2: float,
) -> tuple[int, int, int, float, float, float, bool]:
    hidden = _positive_int(schedule.get("hidden_size"), "schedule hidden_size")
    heads = _positive_int(schedule.get("attention_heads"), "schedule attention_heads")
    kv_heads = _positive_int(schedule.get("kv_heads"), "schedule kv_heads")
    head_dim = hidden // heads
    dense_area_um2 = _positive(dense_qkv_tile.get("area_um2"), "dense_qkv_tile area_um2")
    budget_um2 = _positive(schedule.get("compute_budget_um2"), "schedule compute_budget_um2")
    logic_area_used_um2 = _nonnegative(schedule.get("logic_area_used_um2"), "schedule logic_area_used_um2")
    compute_area_um2 = _nonnegative(schedule.get("compute_area_um2"), "schedule compute_area_um2")
    retained_noncompute_logic_um2 = logic_area_used_um2 - compute_area_um2
    if retained_noncompute_logic_um2 < 0.0:
        raise ValueError("schedule retained noncompute logic area must be nonnegative")
    qkv_useful_limit = hidden // 8 + 2 * kv_heads * head_dim // 8
    dense_count = min(
        qkv_useful_limit,
        max(0, math.floor((budget_um2 - retained_noncompute_logic_um2 - service_area_um2) / dense_area_um2)),
    )
    logic_area_um2 = retained_noncompute_logic_um2 + service_area_um2 + dense_count * dense_area_um2
    area_fit = dense_count > 0 and logic_area_um2 <= budget_um2 + 1e-9
    shared_sram_um2 = _nonnegative(
        schedule.get("measured_shared_sram_used_area_um2", 0.0),
        "schedule measured_shared_sram_used_area_um2",
    )
    tile_sram_um2 = _nonnegative(
        schedule.get("measured_tile_local_sram_area_um2", 0.0),
        "schedule measured_tile_local_sram_area_um2",
    )
    return (
        dense_count,
        qkv_useful_limit,
        retained_noncompute_logic_um2,
        logic_area_um2,
        shared_sram_um2,
        tile_sram_um2,
        area_fit,
    )


def _measured_row(
    *,
    schedule: JsonDict,
    dense_qkv_tile: JsonDict,
    prior_row: JsonDict,
    service_activity: JsonDict,
    online_exact_baseline: JsonDict,
) -> JsonDict:
    case_id = str(service_activity["case_id"])
    cluster_count = int(service_activity["cluster_count"])
    hidden = _positive_int(schedule.get("hidden_size"), "schedule hidden_size")
    heads = _positive_int(schedule.get("attention_heads"), "schedule attention_heads")
    kv_heads = _positive_int(schedule.get("kv_heads"), "schedule kv_heads")
    layers = _positive_int(schedule.get("layers"), "schedule layers")
    sequence_length = _positive_int(schedule.get("sequence_length"), "schedule sequence_length")
    prior_microkernel_cycle = _positive_int(
        prior_row.get("service_calibration_microkernel_integrated_completion_cycle"),
        f"prior c{cluster_count} service_calibration_microkernel_integrated_completion_cycle",
    )
    activity_contract = service_activity["activity_contract"]
    service_window = service_activity["service_window"]
    measured_cycle_count = _positive_int(service_window.get("cycle_count"), "service window cycle_count")
    if measured_cycle_count != _positive_int(
        activity_contract.get("cycle_count"),
        "service activity cycle_count",
    ):
        raise ValueError("service window cycle_count does not match service activity cycle_count")
    if measured_cycle_count != prior_microkernel_cycle:
        raise ValueError(
            f"service activity cycle_count / service VCD microkernel cycle_count does not match prior c{cluster_count} calibration cycle"
        )
    service_area_um2 = _positive(
        service_activity["authoritative_service_ppa"].get("instance_area_um2"),
        "authoritative service area",
    )
    service_power_mw = _positive(
        service_activity["authoritative_service_ppa"].get("total_power_mw"),
        "authoritative service total_power_mw",
    )
    service_critical_path_ns = _positive(
        service_activity["authoritative_service_ppa"].get("critical_path_ns"),
        "authoritative service critical_path_ns",
    )
    service_die_area_um2 = _positive(
        service_activity["authoritative_service_ppa"].get("die_area"),
        "authoritative service die_area",
    )
    (
        dense_count,
        qkv_useful_limit,
        retained_noncompute_logic_um2,
        logic_area_um2,
        shared_sram_um2,
        tile_sram_um2,
        area_fit,
    ) = _recompute_dense_tiles(
        schedule=schedule,
        dense_qkv_tile=dense_qkv_tile,
        service_area_um2=service_area_um2,
    )
    dense_macs = _positive(dense_qkv_tile.get("effective_macs_per_cycle"), "dense_qkv_tile effective_macs_per_cycle")
    head_dim = hidden // heads
    qkv_work = hidden**2 + 2 * hidden * kv_heads * head_dim
    qkv_cycles = math.ceil(qkv_work / (dense_count * dense_macs)) if dense_count else None
    cluster_waves_per_layer = _positive_int(
        prior_row.get("cluster_waves_per_layer"),
        f"prior c{cluster_count} cluster_waves_per_layer",
    )
    service_cycles_per_wave = _positive_int(
        prior_row.get("service_calibrated_full_context_cycles_per_wave"),
        f"prior c{cluster_count} service_calibrated_full_context_cycles_per_wave",
    )
    attention_cycles = cluster_waves_per_layer * service_cycles_per_wave
    fixed_cycles = _nonnegative_int(prior_row.get("fixed_cycles"), f"prior c{cluster_count} fixed_cycles")
    layer_cycles = qkv_cycles + attention_cycles + fixed_cycles if qkv_cycles is not None else None
    total_cycles = layer_cycles * layers if layer_cycles is not None else None
    prior_clock_ns = _positive(prior_row.get("clock_ns"), f"prior c{cluster_count} clock_ns")
    clock_ns = max(prior_clock_ns, _EXPECTED_SERVICE_CLOCK_NS)
    latency_us = total_cycles * clock_ns / 1000.0 if total_cycles is not None else None
    timing_feasible = (
        _positive(
            service_activity["authoritative_service_ppa"].get("critical_path_ns"),
            "authoritative service critical_path_ns",
        )
        <= clock_ns
    )

    microkernel_duration_s = _positive(service_window.get("duration_s"), "service window duration_s")
    service_duration_s = service_cycles_per_wave * clock_ns * 1.0e-9
    dynamic_j = _positive(service_window.get("energy_j", {}).get("dynamic"), "service window dynamic energy")
    leakage_j = _positive(service_window.get("energy_j", {}).get("leakage"), "service window leakage energy")
    workload_contract = service_activity["workload_contract"]
    active_context_tokens = _positive_int(
        workload_contract.get("active_context_tokens"),
        "workload_contract active_context_tokens",
    )
    measured_context_capacity_tokens = _positive_int(
        workload_contract.get("max_context_capacity_tokens"),
        "workload_contract max_context_capacity_tokens",
    )
    full_measured_window_count = math.ceil(sequence_length / active_context_tokens)
    full_measured_window_count_exact = sequence_length // active_context_tokens
    final_partial_tokens = sequence_length % active_context_tokens
    full_context_dynamic_per_service_wave_j = dynamic_j * full_measured_window_count
    full_context_leakage_per_service_wave_j = leakage_j * (service_duration_s / microkernel_duration_s)
    full_context_component_per_service_wave_j = (
        full_context_dynamic_per_service_wave_j + full_context_leakage_per_service_wave_j
    )
    full_service_wave_count = cluster_waves_per_layer * layers
    component_dynamic_j = full_context_dynamic_per_service_wave_j * full_service_wave_count
    component_leakage_j = full_context_leakage_per_service_wave_j * full_service_wave_count
    component_total_j = full_context_component_per_service_wave_j * full_service_wave_count
    prior_cluster_area_mm2 = _positive(prior_row.get("cluster_area_mm2"), f"prior c{cluster_count} cluster_area_mm2")
    token_throughput_per_s = round(1.0e6 / latency_us, 12) if latency_us else None
    comparison = {
        "baseline_model": online_exact_baseline["model"],
        "baseline_decision": online_exact_baseline["decision"],
        "full_token_latency_directly_comparable": latency_us is not None,
        "full_token_throughput_directly_comparable": token_throughput_per_s is not None,
        "energy_directly_comparable": False,
        "power_scope_note": (
            "This row carries composed-service routed total_power_mw and service-window average power, while the "
            "online-exact baseline carries compute power and local-reducer macro-only power; no direct total-token "
            "power comparison is claimed."
        ),
        "latency_ratio_vs_online_exact_single_clock_strict_upper_bound": (
            round(latency_us / online_exact_baseline["single_clock_strict_latency_upper_bound_us"], 12)
            if latency_us is not None
            else None
        ),
        "throughput_ratio_vs_online_exact_single_clock_strict_lower_bound": (
            round(
                token_throughput_per_s / online_exact_baseline["single_clock_strict_throughput_lower_bound_per_s"],
                12,
            )
            if token_throughput_per_s is not None
            else None
        ),
        "latency_ratio_vs_online_exact_dual_clock_strict_upper_bound": (
            round(latency_us / online_exact_baseline["dual_clock_strict_latency_upper_bound_us"], 12)
            if latency_us is not None
            else None
        ),
        "throughput_ratio_vs_online_exact_dual_clock_strict_lower_bound": (
            round(
                token_throughput_per_s / online_exact_baseline["dual_clock_strict_throughput_lower_bound_per_s"],
                12,
            )
            if token_throughput_per_s is not None
            else None
        ),
        "embodied_area_ratio_vs_online_exact_replica_recost_embodied_area": round(
            ((logic_area_um2 + shared_sram_um2 + tile_sram_um2) / 1.0e6)
            / online_exact_baseline["replica_recost_embodied_logic_plus_existing_shared_tile_sram_area_mm2"],
            12,
        ),
        "service_instance_area_ratio_vs_online_exact_macro_only_area_scaled_16_clusters": round(
            (service_area_um2 / 1.0e6) / online_exact_baseline["macro_only_area_mm2_scaled_16_clusters"],
            12,
        ),
        "service_total_power_ratio_vs_online_exact_macro_only_power_scaled_16_clusters": round(
            service_power_mw / online_exact_baseline["macro_only_power_mw_scaled_16_clusters"],
            12,
        ),
        "service_total_power_ratio_vs_online_exact_replica_recost_compute_power": round(
            service_power_mw / online_exact_baseline["replica_recost_compute_power_mw"],
            12,
        ),
        "online_exact_energy_comparison_status": "not_available_no_total_token_energy_claim_in_online_exact_baseline",
    }

    row = {
        "candidate_id": f"decode_score_multivalue_service_measured_c{cluster_count}",
        "source_prior_candidate_id": _string(prior_row.get("candidate_id"), f"prior c{cluster_count} candidate_id"),
        "cluster_count": cluster_count,
        "status": f"directly_measured_c{cluster_count}_anchor",
        "promoted": True,
        "rankable_as_measured": True,
        "measurement_scope": f"strict_c{cluster_count}_activity_backed_microkernel_scaled_composed_service_anchor",
        "service_calibration_case_id": case_id,
        "service_calibration_microkernel_integrated_completion_cycle": prior_microkernel_cycle,
        "service_activity_microkernel_cycle_count": measured_cycle_count,
        "service_no_stall_full_context_cycles_per_wave": _positive_int(
            prior_row.get("service_no_stall_full_context_cycles_per_wave"),
            f"prior c{cluster_count} service_no_stall_full_context_cycles_per_wave",
        ),
        "service_calibrated_full_context_cycles_per_wave": service_cycles_per_wave,
        "service_cycle_source": f"preserved_from_prior_c{cluster_count}_full_context_calibration",
        "cluster_waves_per_layer": cluster_waves_per_layer,
        "head_commands_per_layer": _positive_int(
            prior_row.get("head_commands_per_layer"),
            f"prior c{cluster_count} head_commands_per_layer",
        ),
        "dense_qkv_tile_count": dense_count,
        "dense_qkv_useful_parallelism_limit": qkv_useful_limit,
        "qkv_cycles": qkv_cycles,
        "attention_cycles": attention_cycles,
        "fixed_cycles": fixed_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "prior_clock_ns": prior_clock_ns,
        "measured_service_clock_ns": _EXPECTED_SERVICE_CLOCK_NS,
        "clock_ns": clock_ns,
        "latency_us": round(latency_us, 6) if latency_us is not None else None,
        "token_throughput_per_s": token_throughput_per_s,
        "prior_cluster_area_mm2": round(prior_cluster_area_mm2, 9),
        "authoritative_composed_service_area_mm2": round(service_area_um2 / 1.0e6, 9),
        "authoritative_composed_service_die_area_mm2": round(service_die_area_um2 / 1.0e6, 9),
        "authoritative_composed_service_total_power_mw": round(service_power_mw, 9),
        "authoritative_composed_service_critical_path_ns": round(service_critical_path_ns, 9),
        "area_replacement_delta_mm2": round(service_area_um2 / 1.0e6 - prior_cluster_area_mm2, 9),
        "dense_qkv_area_mm2": round(
            dense_count * _positive(dense_qkv_tile.get("area_um2"), "dense_qkv_tile area_um2") / 1.0e6,
            9,
        ),
        "retained_noncompute_logic_area_mm2": round(retained_noncompute_logic_um2 / 1.0e6, 9),
        "logic_area_mm2": round(logic_area_um2 / 1.0e6, 9),
        "existing_shared_sram_area_mm2": round(shared_sram_um2 / 1.0e6, 9),
        "existing_tile_local_sram_area_mm2": round(tile_sram_um2 / 1.0e6, 9),
        "embodied_logic_plus_existing_shared_tile_sram_area_mm2": round(
            (logic_area_um2 + shared_sram_um2 + tile_sram_um2) / 1.0e6,
            9,
        ),
        "compute_budget_slack_mm2": round(
            (_positive(schedule.get("compute_budget_um2"), "schedule compute_budget_um2") - logic_area_um2)
            / 1.0e6,
            9,
        ),
        "compute_budget_area_fit": area_fit,
        "timing_feasible": timing_feasible,
        "area_replacement_provenance": (
            f"Authoritative composed c{cluster_count} total instance area replaces the prior c{cluster_count} cluster total instance area. "
            "The 16KiB service value store remains counted inside the service instance area as a "
            "command-working-set macro component, and broader schedule shared/tile SRAM remains separately charged."
        ),
        "measured_window_active_context_tokens": active_context_tokens,
        "measured_window_context_capacity_tokens": measured_context_capacity_tokens,
        "full_measured_window_count": full_measured_window_count,
        "full_measured_window_count_exact": full_measured_window_count_exact,
        "final_partial_tokens": final_partial_tokens,
        "final_partial_window_conservatively_charged_as_full_measured_window": final_partial_tokens > 0,
        "service_window_duration_s": microkernel_duration_s,
        "full_context_service_duration_s_per_service_wave": service_duration_s,
        "full_context_service_duration_s_per_head_command": service_duration_s,
        "full_context_service_wave_count": full_service_wave_count,
        "service_window_dynamic_energy_j": dynamic_j,
        "service_window_leakage_energy_j": leakage_j,
        "service_window_average_dynamic_power_mw": dynamic_j / microkernel_duration_s * 1.0e3,
        "service_window_average_leakage_power_mw": leakage_j / microkernel_duration_s * 1.0e3,
        "service_window_average_dynamic_plus_leakage_power_mw": (dynamic_j + leakage_j)
        / microkernel_duration_s
        * 1.0e3,
        "full_context_dynamic_energy_j_per_service_wave": full_context_dynamic_per_service_wave_j,
        "full_context_leakage_energy_j_per_service_wave": full_context_leakage_per_service_wave_j,
        "service_component_dynamic_energy_mj_per_token": component_dynamic_j * 1.0e3,
        "service_component_leakage_energy_mj_per_token": component_leakage_j * 1.0e3,
        "service_component_energy_mj_per_token": component_total_j * 1.0e3,
        "service_window_energy_accounting": "whole_measured_service_window_scaled_by_measured_windows_and_service_waves",
        "direct_total_token_energy": False,
        "energy_status": (
            "activity_backed_microkernel_scaled_composed_service_component_estimate_"
            "not_direct_total_token_energy"
        ),
        "energy_scope_exclusions": [
            "legacy cluster dynamic energy is excluded",
            "HBM/DRAM energy is excluded",
            "broader SRAM and NoC energy are excluded",
            "producer and dense QKV activity energy are excluded",
        ],
        "comparison_to_online_exact_measured_reducer": comparison,
    }
    if cluster_count == 1:
        row["full_context_dynamic_energy_j_per_head_command"] = full_context_dynamic_per_service_wave_j
        row["full_context_leakage_energy_j_per_head_command"] = full_context_leakage_per_service_wave_j
    return row


def _dominates(lhs: JsonDict, rhs: JsonDict) -> bool:
    objective_keys = (
        "latency_us",
        "embodied_logic_plus_existing_shared_tile_sram_area_mm2",
        "service_component_energy_mj_per_token",
    )
    lhs_values = [float(lhs[key]) for key in objective_keys]
    rhs_values = [float(rhs[key]) for key in objective_keys]
    return all(left <= right for left, right in zip(lhs_values, rhs_values)) and any(
        left < right for left, right in zip(lhs_values, rhs_values)
    )


def _pareto_rows(rows: list[JsonDict]) -> list[JsonDict]:
    pareto: list[JsonDict] = []
    for candidate in rows:
        if any(_dominates(other, candidate) for other in rows if other is not candidate):
            continue
        pareto.append(candidate)
    return sorted(pareto, key=lambda row: (float(row["latency_us"]), int(row["cluster_count"])))


def _blocked_row(row: JsonDict, *, blocker: str | None = None) -> JsonDict:
    return {
        "candidate_id": f"{_string(row.get('candidate_id'), 'prior row candidate_id')}_blocked_pending_measured_service",
        "source_prior_candidate_id": _string(row.get("candidate_id"), "prior row candidate_id"),
        "cluster_count": _positive_int(row.get("cluster_count"), "prior row cluster_count"),
        "status": "blocked_unpromoted_pending_equivalent_composed_physical_activity_evidence",
        "promoted": False,
        "rankable_as_measured": False,
        "measurement_scope": "not_measured",
        "blocker": blocker
        or (
            "Only directly measured composed physical/activity anchors are promoted. "
            "Equivalent composed physical area and activity-backed service evidence is still required for this cluster count."
        ),
    }


def build_report(
    *,
    prior_cluster_frontier_json: Path,
    online_exact_measured_reducer_json: Path,
    service_activity_power_json: Path | None = None,
    service_activity_power_jsons: list[Path] | None = None,
) -> JsonDict:
    prior = _load(prior_cluster_frontier_json)
    online_exact_baseline = _validated_online_exact_measured_reducer(_load(online_exact_measured_reducer_json))
    selected_service_paths = list(service_activity_power_jsons or [])
    if service_activity_power_json is not None:
        selected_service_paths.append(service_activity_power_json)
    if not selected_service_paths:
        raise ValueError("at least one service_activity_power_json is required")
    (
        schedule,
        schedule_source,
        dense_qkv_tile,
        prior_rows_by_cluster,
        prior_rows,
        prior_precision,
        workload_contract,
    ) = _validated_prior_frontier(
        prior,
        prior_cluster_frontier_json,
    )
    validated_service_activities: dict[int, JsonDict] = {}
    portable_service_inputs: list[str] = []
    for service_path in selected_service_paths:
        validated = _validated_service_activity(
            _load(service_path),
            prior_precision,
            workload_contract,
        )
        cluster_count = int(validated["cluster_count"])
        if cluster_count in validated_service_activities:
            raise ValueError(f"duplicate measured service activity supplied for c{cluster_count}")
        validated_service_activities[cluster_count] = validated
        portable_service_inputs.append(_portable_path(service_path))
    if 1 not in validated_service_activities:
        raise ValueError("a strict c1 service activity-power report is required")

    c1_measured = _measured_row(
        schedule=schedule,
        dense_qkv_tile=dense_qkv_tile,
        prior_row=prior_rows_by_cluster[1],
        service_activity=validated_service_activities[1],
        online_exact_baseline=online_exact_baseline,
    )
    if not c1_measured["compute_budget_area_fit"] or not c1_measured["timing_feasible"]:
        raise ValueError("recomputed c1 measured anchor is not feasible for promotion")

    promoted_rows = [c1_measured]
    rows: list[JsonDict] = []
    blocked_rows: list[JsonDict] = []
    for prior_row in prior_rows:
        cluster_count = _positive_int(prior_row.get("cluster_count"), "prior row cluster_count")
        if cluster_count == 1:
            rows.append(c1_measured)
            continue
        service_activity = validated_service_activities.get(cluster_count)
        if service_activity is None:
            blocked = _blocked_row(
                prior_row,
                blocker=(
                    "Strict activity-backed composed-service physical evidence is still required "
                    f"before c{cluster_count} can be promoted."
                ),
            )
            rows.append(blocked)
            blocked_rows.append(blocked)
            continue
        measured_row = _measured_row(
            schedule=schedule,
            dense_qkv_tile=dense_qkv_tile,
            prior_row=prior_row,
            service_activity=service_activity,
            online_exact_baseline=online_exact_baseline,
        )
        if measured_row["compute_budget_area_fit"] and measured_row["timing_feasible"]:
            rows.append(measured_row)
            promoted_rows.append(measured_row)
        else:
            blocked = _blocked_row(
                prior_row,
                blocker=(
                    f"Strict c{cluster_count} activity/physical evidence was supplied, but the recomputed "
                    "composed-service point is not feasible for promotion under the measured schedule budget."
                ),
            )
            rows.append(blocked)
            blocked_rows.append(blocked)

    best_anchor = max(promoted_rows, key=lambda row: float(row["token_throughput_per_s"]))
    c2_promoted = any(row["cluster_count"] == 2 for row in promoted_rows)
    pareto_rows = _pareto_rows(promoted_rows) if c2_promoted else []
    c1_service = validated_service_activities[1]
    c1_contract = _service_case(c1_service["case_id"])
    selected_candidates = {
        f"c{cluster_count}": {
            "candidate_id": _string(service_activity["best"].get("candidate_id"), "service best candidate_id"),
            "flow_variant": _string(service_activity["best"].get("flow_variant"), "service best flow_variant"),
            "integrated_service_hashes": service_activity["integrated_hashes"],
            "activity_contract": {
                "clock_period_ns": _positive(
                    service_activity["activity_contract"].get("clock_period_ns"),
                    "service activity clock_period_ns",
                ),
                "cycle_count": _positive_int(
                    service_activity["activity_contract"].get("cycle_count"),
                    "service activity cycle_count",
                ),
            },
            "activity_workload_contract": service_activity["workload_contract"],
            "macro_activity_contract": service_activity["macro_activity_contract"],
        }
        for cluster_count, service_activity in sorted(validated_service_activities.items())
    }
    service_contracts = {
        f"c{cluster_count}": {
            "model": _EXPECTED_SERVICE_MODEL,
            "decision": _EXPECTED_SERVICE_DECISION,
            "promotion_gate_pass": True,
            "required_flow_variant": service_activity["flow_variant"],
            "required_design": service_activity["design"],
            "required_platform": _EXPECTED_SERVICE_PLATFORM,
            "required_clock_period_ns": _EXPECTED_SERVICE_CLOCK_NS,
        }
        for cluster_count, service_activity in sorted(validated_service_activities.items())
    }
    return {
        "version": 1,
        "model": _MODEL,
        "decision": (
            "strict_c1_c2_measured_service_anchors_promoted_c3plus_blocked"
            if c2_promoted
            else "strict_c1_measured_service_anchor_promoted_c2plus_blocked"
        ),
        "inputs": {
            "prior_cluster_frontier_json": _portable_path(prior_cluster_frontier_json),
            "online_exact_measured_reducer_json": _portable_path(online_exact_measured_reducer_json),
            "service_activity_power_json": portable_service_inputs[0],
            "service_activity_power_jsons": portable_service_inputs,
            "source_schedule_json": schedule_source,
        },
        "prior_cluster_frontier_contract": {
            "model": _EXPECTED_PRIOR_MODEL,
            "decision": _EXPECTED_PRIOR_DECISION,
            "promotion_status": _EXPECTED_PRIOR_PROMOTION,
            "expected_item_id_if_present": _EXPECTED_PRIOR_ITEM_ID,
        },
        "service_activity_power_contract": {
            "model": _EXPECTED_SERVICE_MODEL,
            "decision": _EXPECTED_SERVICE_DECISION,
            "promotion_gate_pass": True,
            "required_flow_variant": c1_contract["flow_variant"],
            "required_design": c1_contract["design"],
            "required_platform": _EXPECTED_SERVICE_PLATFORM,
            "required_clock_period_ns": _EXPECTED_SERVICE_CLOCK_NS,
        },
        "service_activity_power_contracts": service_contracts,
        "schedule_contract": {
            "hidden_size": _positive_int(schedule.get("hidden_size"), "schedule hidden_size"),
            "attention_heads": _positive_int(schedule.get("attention_heads"), "schedule attention_heads"),
            "kv_heads": _positive_int(schedule.get("kv_heads"), "schedule kv_heads"),
            "layers": _positive_int(schedule.get("layers"), "schedule layers"),
            "sequence_length": _positive_int(schedule.get("sequence_length"), "schedule sequence_length"),
            "workload_contract": dict(workload_contract),
            "measured_window_active_context_tokens": c1_measured["measured_window_active_context_tokens"],
            "measured_window_context_capacity_tokens": c1_measured["measured_window_context_capacity_tokens"],
            "full_measured_window_count": c1_measured["full_measured_window_count"],
            "full_measured_window_count_exact": c1_measured["full_measured_window_count_exact"],
            "final_partial_tokens": c1_measured["final_partial_tokens"],
            "full_head_commands_per_token": _EXPECTED_HEADS * _EXPECTED_LAYERS,
        },
        "selected_service_activity_candidate": selected_candidates["c1"],
        "selected_service_activity_candidates": selected_candidates,
        "online_exact_measured_reducer_baseline": online_exact_baseline,
        "online_exact_measured_reducer_comparison": {
            "dependency_job_sequence": [
                "c1 PNR",
                "c1 activity power",
                "measured frontier",
            ],
            "baseline_scope": (
                "merged online-exact measured-reducer recost with strict single-clock and dual-clock upper/lower "
                "throughput bounds plus routed macro-only area/power."
            ),
            "full_token_latency_comparison_scope": "direct",
            "full_token_throughput_comparison_scope": "direct",
            "energy_comparison_scope": "not_directly_comparable",
            "power_comparison_scope": "service_power_vs_baseline_component_power_only",
            "preserved_measured_window_scaling": (
                "The measured c1 service window is scaled with ceil(sequence_length / 24), while the 128-token context "
                "capacity remains reported separately and is not used as the scaling divisor."
            ),
            "promoted_candidate_ids": [row["candidate_id"] for row in promoted_rows],
        },
        "precision": {
            "status": _EXPECTED_SERVICE_PRECISION_STATUS,
            "decision": _EXPECTED_PRIOR_PRECISION_DECISION,
            "score_tensor_hash": _string(prior_precision.get("score_tensor_hash"), "prior precision score_tensor_hash"),
            "final_tensor_hash": _string(prior_precision.get("final_tensor_hash"), "prior precision final_tensor_hash"),
            "quality_change": "none_exact_integer_semantics_preserved",
        },
        "rows": rows,
        "promoted_rows": promoted_rows,
        "blocked_rows": blocked_rows,
        "best_measured_anchor": best_anchor,
        **({"best_throughput_candidate": best_anchor, "pareto_rows": pareto_rows} if c2_promoted else {}),
        "promotion_status": (
            "strict_c1_c2_measured_anchors_promoted_c3plus_unpromoted_pending_equivalent_composed_physical_activity_evidence"
            if c2_promoted
            else "strict_c1_measured_anchor_promoted_c2plus_unpromoted_pending_equivalent_composed_physical_activity_evidence"
        ),
        "remaining_abstractions": [
            (
                "This report promotes only directly measured composed-service anchors. "
                + ("c1 and c2 are promoted; c3+ remain blocked." if c2_promoted else "Only c1 is promoted; c2+ remain blocked.")
            ),
            (
                "When multiple measured anchors are promoted, best_throughput_candidate is reported separately and pareto_rows define"
                " the non-dominated latency/embodied-area/service-energy frontier."
                if c2_promoted
                else "best_measured_anchor remains the sole promoted c1 anchor in the c1-only path."
            ),
            "The activity-backed energy is a microkernel-scaled composed-service component estimate, not direct total-token energy.",
            "Measured whole-service window energy is scaled with ceil(sequence_length / 24) and then multiplied by cluster_waves_per_layer * layers; c2 must not be multiplied by heads * layers.",
            "The 128-token measured window capacity remains a distinct capacity fact; it does not replace the explicit ceil(sequence_length / 24) scaling divisor.",
            "Comparison against the merged online-exact measured-reducer recost is direct for full-token latency/throughput, but energy is not directly comparable because the online-exact baseline does not claim total-token energy.",
            "HBM/DRAM, broader SRAM/NoC, producer, and dense-QKV activity energy remain outside this report.",
            "The 16KiB service value store remains counted inside the service instance area, while broader schedule SRAM remains separately charged.",
            (
                "c3+ rows remain blocked until equivalent composed physical/activity evidence exists for those cluster counts."
                if c2_promoted
                else "c2+ rows remain blocked until equivalent composed physical/activity evidence exists for those cluster counts."
            ),
        ],
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    anchor = payload.get("best_throughput_candidate", payload["best_measured_anchor"])
    anchor_label = "best throughput candidate" if "best_throughput_candidate" in payload else "best measured anchor"
    lines = [
        "# Llama7B measured composed-service frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- {anchor_label}: `{anchor['candidate_id']}`",
        f"- clock ns: `{anchor['clock_ns']}`",
        f"- latency us: `{anchor['latency_us']}`",
        f"- dense QKV tiles: `{anchor['dense_qkv_tile_count']}`",
        f"- service routed total power mW: `{anchor['authoritative_composed_service_total_power_mw']}`",
        f"- service-window avg dynamic+leakage power mW: `{anchor['service_window_average_dynamic_plus_leakage_power_mw']}`",
        (
            "- area replacement: prior cluster `{prior}` mm2 -> composed service `{new}` mm2".format(
                prior=anchor["prior_cluster_area_mm2"],
                new=anchor["authoritative_composed_service_area_mm2"],
            )
        ),
        (
            "- online-exact dual-clock strict upper/lower baseline: `{lat}` us / `{thr}` token/s".format(
                lat=payload["online_exact_measured_reducer_baseline"]["dual_clock_strict_latency_upper_bound_us"],
                thr=payload["online_exact_measured_reducer_baseline"]["dual_clock_strict_throughput_lower_bound_per_s"],
            )
        ),
        (
            "- service component energy: `{total}` mJ/token "
            "(dynamic `{dynamic}`, leakage `{leakage}`)".format(
                total=anchor["service_component_energy_mj_per_token"],
                dynamic=anchor["service_component_dynamic_energy_mj_per_token"],
                leakage=anchor["service_component_leakage_energy_mj_per_token"],
            )
        ),
        "- total-token energy: `not directly measured here`",
        "",
    ]
    if "pareto_rows" in payload:
        lines.append(f"- pareto rows: `{', '.join(row['candidate_id'] for row in payload['pareto_rows'])}`")
        lines.append("")
    lines.extend(
        [
            "| candidate | clusters | status | promoted | rankable | latency us | area mm2 | service component mJ/token |",
        "|---|---:|---|---|---|---:|---:|---:|",
        ]
    )
    for row in payload["rows"]:
        area = row.get("embodied_logic_plus_existing_shared_tile_sram_area_mm2")
        energy = row.get("service_component_energy_mj_per_token")
        lines.append(
            f"| {row['candidate_id']} | {row['cluster_count']} | {row['status']} | "
            f"{row['promoted']} | {row['rankable_as_measured']} | {row.get('latency_us')} | "
            f"{area if area is not None else 'blocked'} | {energy if energy is not None else 'blocked'} |"
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-cluster-frontier-json", type=Path, required=True)
    parser.add_argument("--online-exact-measured-reducer-json", type=Path, required=True)
    parser.add_argument("--service-activity-power-json", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        prior_cluster_frontier_json=args.prior_cluster_frontier_json,
        online_exact_measured_reducer_json=args.online_exact_measured_reducer_json,
        service_activity_power_jsons=args.service_activity_power_json,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

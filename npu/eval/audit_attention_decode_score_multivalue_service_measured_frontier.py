#!/usr/bin/env python3
"""Compose a strict c1 measured-service frontier anchor for Llama7B decode."""

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
_EXPECTED_SERVICE_FLOW_VARIANT = "decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1"
_EXPECTED_SERVICE_DESIGN = "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr"
_EXPECTED_SERVICE_PLATFORM = "nangate45"
_EXPECTED_SERVICE_MACRO_COUNTS = {
    "fakeram45_2048x39": 56,
    "fakeram45_64x32": 64,
}
_EXPECTED_SERVICE_MACRO_PROFILE = "multivalue_service_c1_v1"
_EXPECTED_CASE_ID = "c1_p128_b4_rr"
_EXPECTED_SERVICE_CONFIG = {
    "cluster_count": 1,
    "packet_w": 128,
    "banks": 4,
    "req_queue_depth": 4,
    "resp_queue_depth": 4,
    "bank_queue_depth": 4,
    "read_latency": 2,
    "arb_mode": "round_robin",
    "locality_burst_max": 2,
}
_EXPECTED_HIDDEN = 4096
_EXPECTED_HEADS = 32
_EXPECTED_KV_HEADS = 4
_EXPECTED_LAYERS = 32
_EXPECTED_SERVICE_CLOCK_NS = 10.0
_EXPECTED_WORKLOAD_CONTRACT = {
    "command_block_count": 3,
    "context_tokens_per_block": 8,
    "active_context_tokens": 24,
    "max_blocks": 16,
    "max_context_capacity_tokens": 128,
    "value_dim": 128,
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


def _validated_prior_frontier(
    prior: JsonDict, prior_frontier_json: Path
) -> tuple[JsonDict, str, JsonDict, JsonDict, list[JsonDict], JsonDict]:
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
    c1_rows = [
        row
        for row in rows
        if _positive_int(row.get("cluster_count"), "prior frontier cluster_count") == 1
    ]
    if len(c1_rows) != 1:
        raise ValueError("prior frontier must contain exactly one c1 row")
    c1_row = c1_rows[0]
    if _string(c1_row.get("service_calibration_case_id"), "prior c1 service_calibration_case_id") != _EXPECTED_CASE_ID:
        raise ValueError("prior frontier c1 service_calibration_case_id mismatch")
    _positive_int(
        c1_row.get("service_calibration_microkernel_integrated_completion_cycle"),
        "prior c1 service_calibration_microkernel_integrated_completion_cycle",
    )
    if _positive_int(c1_row.get("cluster_waves_per_layer"), "prior c1 cluster_waves_per_layer") != _EXPECTED_HEADS:
        raise ValueError("prior frontier c1 cluster_waves_per_layer mismatch")
    if _positive_int(c1_row.get("head_commands_per_layer"), "prior c1 head_commands_per_layer") != _EXPECTED_HEADS:
        raise ValueError("prior frontier c1 head_commands_per_layer mismatch")
    _positive_int(
        c1_row.get("service_no_stall_full_context_cycles_per_wave"),
        "prior c1 service_no_stall_full_context_cycles_per_wave",
    )
    _positive_int(
        c1_row.get("service_calibrated_full_context_cycles_per_wave"),
        "prior c1 service_calibrated_full_context_cycles_per_wave",
    )
    _nonnegative_int(c1_row.get("fixed_cycles"), "prior c1 fixed_cycles")
    _positive(c1_row.get("clock_ns"), "prior c1 clock_ns")
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
    return schedule, schedule_source, dense_qkv_tile, c1_row, rows, precision, workload_contract


def _validated_service_activity(
    service_report: JsonDict,
    prior_precision: JsonDict,
    prior_workload_contract: JsonDict,
) -> tuple[JsonDict, JsonDict, JsonDict, JsonDict, JsonDict, JsonDict, JsonDict]:
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
    if _string(best.get("flow_variant"), "service best flow_variant") != _EXPECTED_SERVICE_FLOW_VARIANT:
        raise ValueError("service best flow_variant mismatch")
    metric = best.get("ppa_metric")
    if not isinstance(metric, dict):
        raise ValueError("service best lacks ppa_metric")
    if _string(metric.get("design"), "service best design") != _EXPECTED_SERVICE_DESIGN:
        raise ValueError("service best design mismatch")
    if _string(metric.get("platform"), "service best platform") != _EXPECTED_SERVICE_PLATFORM:
        raise ValueError("service best platform mismatch")
    params_json = json.loads(_string(metric.get("params_json"), "service best params_json"))
    if not isinstance(params_json, dict):
        raise ValueError("service best params_json is not an object")
    if _string(params_json.get("FLOW_VARIANT"), "service best FLOW_VARIANT") != _EXPECTED_SERVICE_FLOW_VARIANT:
        raise ValueError("service best FLOW_VARIANT mismatch")
    if abs(_positive(params_json.get("CLOCK_PERIOD"), "service best CLOCK_PERIOD") - _EXPECTED_SERVICE_CLOCK_NS) > 1e-9:
        raise ValueError("service best CLOCK_PERIOD mismatch")
    if _positive(metric.get("critical_path_ns"), "service best critical_path_ns") > _EXPECTED_SERVICE_CLOCK_NS:
        raise ValueError("service best is not timing-feasible at 10 ns")
    authoritative = best.get("authoritative_composed_c1_total_ppa")
    if not isinstance(authoritative, dict):
        raise ValueError("service best lacks authoritative_composed_c1_total_ppa")
    if _positive(authoritative.get("critical_path_ns"), "authoritative service critical_path_ns") > _EXPECTED_SERVICE_CLOCK_NS:
        raise ValueError("authoritative composed c1 total instance is not timing-feasible at 10 ns")
    if not math.isclose(
        _positive(authoritative.get("instance_area_um2"), "authoritative service instance_area_um2"),
        _positive(metric.get("instance_area_um2"), "service best instance_area_um2"),
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("authoritative composed c1 total instance area mismatches service best ppa_metric")
    if not math.isclose(
        _positive(authoritative.get("critical_path_ns"), "authoritative service critical_path_ns"),
        _positive(metric.get("critical_path_ns"), "service best critical_path_ns"),
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("authoritative composed c1 timing mismatches service best ppa_metric")
    counts = service_report.get("macro_manifest_contract")
    if not isinstance(counts, dict) or not isinstance(counts.get("counts"), dict):
        raise ValueError("service report lacks macro_manifest_contract counts")
    macro_counts = counts["counts"]
    if macro_counts != _EXPECTED_SERVICE_MACRO_COUNTS:
        raise ValueError("service macro count contract mismatch")
    macro_activity_contract = service_report.get("macro_activity_contract")
    if not isinstance(macro_activity_contract, dict):
        raise ValueError("service report lacks macro_activity_contract")
    if _string(macro_activity_contract.get("profile"), "service macro_activity profile") != _EXPECTED_SERVICE_MACRO_PROFILE:
        raise ValueError("service macro_activity profile mismatch")
    macro_classes = macro_activity_contract.get("macro_classes")
    if not isinstance(macro_classes, dict):
        raise ValueError("service macro_activity_contract lacks macro_classes")
    if set(macro_classes) != set(_EXPECTED_SERVICE_MACRO_COUNTS):
        raise ValueError("service macro_activity_contract macro_classes mismatch")
    assignment_total = 0
    for macro_name, expected_count in _EXPECTED_SERVICE_MACRO_COUNTS.items():
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
    workload_contract = _validated_workload_contract(
        activity_contract.get("workload_contract"),
        "service activity_contract workload_contract",
    )
    if workload_contract != prior_workload_contract:
        raise ValueError("service activity_contract workload_contract mismatch vs prior probe_contract")
    bank3 = service_report.get("bank3_dynamic_inactivity")
    if not isinstance(bank3, dict):
        raise ValueError("service report lacks bank3_dynamic_inactivity")
    if bank3.get("inactive_banks") != [3]:
        raise ValueError("service report must keep bank3 inactive")
    bank3_statement = _string(bank3.get("statement"), "service bank3 statement")
    if "No artificial activity was injected" not in bank3_statement or "not required to toggle" not in bank3_statement:
        raise ValueError("service report bank3 inactivity must be explicitly unforced")
    service_window = best.get("component_service_window_energy")
    if not isinstance(service_window, dict):
        raise ValueError("service best lacks component_service_window_energy")
    if _string(service_window.get("label"), "service component_service_window_energy label") != "component_service_window_energy":
        raise ValueError("service component_service_window_energy label mismatch")
    if service_window.get("is_total_token_energy") is not False:
        raise ValueError("service component_service_window_energy must not be total-token energy")
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
    integrated_service = dependency_contract.get("integrated_service_c1")
    if not isinstance(integrated_service, dict):
        raise ValueError("service dependency_contract lacks integrated_service_c1")
    if _string(integrated_service.get("case_id"), "service integrated_service_c1 case_id") != _EXPECTED_CASE_ID:
        raise ValueError("service integrated_service_c1 case_id mismatch")
    if _string(integrated_service.get("decision"), "service integrated_service_c1 decision") != "pass":
        raise ValueError("service integrated_service_c1 decision mismatch")
    config = integrated_service.get("config")
    if not isinstance(config, dict):
        raise ValueError("service integrated_service_c1 config is missing")
    for key, expected in _EXPECTED_SERVICE_CONFIG.items():
        config_value = config.get(key)
        if config_value != expected:
            raise ValueError(f"service integrated_service_c1 config mismatch for {key}")
    integrated_workload_contract = _validated_workload_contract(
        integrated_service.get("workload_contract"),
        "service integrated_service_c1 workload_contract",
    )
    if integrated_workload_contract != workload_contract:
        raise ValueError("service integrated_service_c1 workload_contract mismatch vs activity workload_contract")
    for key in ("exact_match", "no_protocol_errors", "no_drop_duplicate_deadlock_timeout", "cycle_bound_ok"):
        if integrated_service.get(key) is not True:
            raise ValueError(f"service integrated_service_c1 {key} gate failed")
    hashes = integrated_service.get("hashes")
    if not isinstance(hashes, dict):
        raise ValueError("service integrated_service_c1 lacks hashes")
    integrated_hashes = {
        "score_hash": _string(hashes.get("score_hash"), "service integrated_service_c1 score_hash"),
        "final_hash": _string(hashes.get("final_hash"), "service integrated_service_c1 final_hash"),
        "request_hash": _string(hashes.get("request_hash"), "service integrated_service_c1 request_hash"),
        "wide_response_matrix_hash": _string(
            hashes.get("wide_response_matrix_hash"),
            "service integrated_service_c1 wide_response_matrix_hash",
        ),
    }
    return best, authoritative, service_window, activity_contract, workload_contract, macro_activity_contract, integrated_hashes


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
    embodied_area_um2 = logic_area_um2 + shared_sram_um2 + tile_sram_um2
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
    prior_c1_row: JsonDict,
    authoritative_service_ppa: JsonDict,
    service_window: JsonDict,
    workload_contract: JsonDict,
) -> JsonDict:
    hidden = _positive_int(schedule.get("hidden_size"), "schedule hidden_size")
    heads = _positive_int(schedule.get("attention_heads"), "schedule attention_heads")
    kv_heads = _positive_int(schedule.get("kv_heads"), "schedule kv_heads")
    layers = _positive_int(schedule.get("layers"), "schedule layers")
    sequence_length = _positive_int(schedule.get("sequence_length"), "schedule sequence_length")
    prior_microkernel_cycle = _positive_int(
        prior_c1_row.get("service_calibration_microkernel_integrated_completion_cycle"),
        "prior c1 service_calibration_microkernel_integrated_completion_cycle",
    )
    measured_cycle_count = _positive_int(service_window.get("cycle_count"), "service window cycle_count")
    if measured_cycle_count != prior_microkernel_cycle:
        raise ValueError("service VCD microkernel cycle_count does not match prior c1 calibration cycle")
    service_area_um2 = _positive(authoritative_service_ppa.get("instance_area_um2"), "authoritative service area")
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
    cluster_waves_per_layer = _positive_int(prior_c1_row.get("cluster_waves_per_layer"), "prior c1 cluster_waves_per_layer")
    service_cycles_per_wave = _positive_int(
        prior_c1_row.get("service_calibrated_full_context_cycles_per_wave"),
        "prior c1 service_calibrated_full_context_cycles_per_wave",
    )
    attention_cycles = cluster_waves_per_layer * service_cycles_per_wave
    fixed_cycles = _nonnegative_int(prior_c1_row.get("fixed_cycles"), "prior c1 fixed_cycles")
    layer_cycles = qkv_cycles + attention_cycles + fixed_cycles if qkv_cycles is not None else None
    total_cycles = layer_cycles * layers if layer_cycles is not None else None
    prior_clock_ns = _positive(prior_c1_row.get("clock_ns"), "prior c1 clock_ns")
    clock_ns = max(prior_clock_ns, _EXPECTED_SERVICE_CLOCK_NS)
    latency_us = total_cycles * clock_ns / 1000.0 if total_cycles is not None else None
    timing_feasible = _positive(authoritative_service_ppa.get("critical_path_ns"), "authoritative service critical_path_ns") <= clock_ns

    microkernel_duration_s = _positive(service_window.get("duration_s"), "service window duration_s")
    service_duration_s = service_cycles_per_wave * clock_ns * 1.0e-9
    dynamic_j = _positive(service_window.get("energy_j", {}).get("dynamic"), "service window dynamic energy")
    leakage_j = _positive(service_window.get("energy_j", {}).get("leakage"), "service window leakage energy")
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
    full_context_dynamic_per_head_j = dynamic_j * full_measured_window_count
    full_context_leakage_per_head_j = leakage_j * (service_duration_s / microkernel_duration_s)
    full_context_component_per_head_j = full_context_dynamic_per_head_j + full_context_leakage_per_head_j
    full_token_commands = heads * layers
    component_dynamic_j = full_context_dynamic_per_head_j * full_token_commands
    component_leakage_j = full_context_leakage_per_head_j * full_token_commands
    component_total_j = full_context_component_per_head_j * full_token_commands
    prior_cluster_area_mm2 = _positive(prior_c1_row.get("cluster_area_mm2"), "prior c1 cluster_area_mm2")

    return {
        "candidate_id": "decode_score_multivalue_service_measured_c1",
        "source_prior_candidate_id": _string(prior_c1_row.get("candidate_id"), "prior c1 candidate_id"),
        "cluster_count": 1,
        "status": "directly_measured_c1_anchor",
        "promoted": True,
        "rankable_as_measured": True,
        "measurement_scope": "strict_c1_activity_backed_microkernel_scaled_composed_service_anchor",
        "service_calibration_case_id": _EXPECTED_CASE_ID,
        "service_calibration_microkernel_integrated_completion_cycle": prior_microkernel_cycle,
        "service_activity_microkernel_cycle_count": measured_cycle_count,
        "service_no_stall_full_context_cycles_per_wave": _positive_int(
            prior_c1_row.get("service_no_stall_full_context_cycles_per_wave"),
            "prior c1 service_no_stall_full_context_cycles_per_wave",
        ),
        "service_calibrated_full_context_cycles_per_wave": service_cycles_per_wave,
        "service_cycle_source": "preserved_from_prior_c1_full_context_calibration",
        "cluster_waves_per_layer": cluster_waves_per_layer,
        "head_commands_per_layer": _positive_int(prior_c1_row.get("head_commands_per_layer"), "prior c1 head_commands_per_layer"),
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
        "token_throughput_per_s": round(1.0e6 / latency_us, 12) if latency_us else None,
        "prior_cluster_area_mm2": round(prior_cluster_area_mm2, 9),
        "authoritative_composed_service_area_mm2": round(service_area_um2 / 1.0e6, 9),
        "area_replacement_delta_mm2": round(service_area_um2 / 1.0e6 - prior_cluster_area_mm2, 9),
        "dense_qkv_area_mm2": round(dense_count * _positive(dense_qkv_tile.get("area_um2"), "dense_qkv_tile area_um2") / 1.0e6, 9),
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
            "Authoritative composed c1 total instance area replaces the prior c1 cluster total instance area. "
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
        "full_context_service_duration_s_per_head_command": service_duration_s,
        "service_window_dynamic_energy_j": dynamic_j,
        "service_window_leakage_energy_j": leakage_j,
        "full_context_dynamic_energy_j_per_head_command": full_context_dynamic_per_head_j,
        "full_context_leakage_energy_j_per_head_command": full_context_leakage_per_head_j,
        "service_component_dynamic_energy_mj_per_token": component_dynamic_j * 1.0e3,
        "service_component_leakage_energy_mj_per_token": component_leakage_j * 1.0e3,
        "service_component_energy_mj_per_token": component_total_j * 1.0e3,
        "energy_status": (
            "activity_backed_microkernel_scaled_composed_service_component_estimate_"
            "not_direct_total_token_energy"
        ),
        "direct_total_token_energy": False,
        "energy_scope_exclusions": [
            "legacy cluster dynamic energy is excluded",
            "HBM/DRAM energy is excluded",
            "broader SRAM and NoC energy are excluded",
            "producer and dense QKV activity energy are excluded",
        ],
    }


def _blocked_row(row: JsonDict) -> JsonDict:
    return {
        "candidate_id": f"{_string(row.get('candidate_id'), 'prior row candidate_id')}_blocked_pending_measured_service",
        "source_prior_candidate_id": _string(row.get("candidate_id"), "prior row candidate_id"),
        "cluster_count": _positive_int(row.get("cluster_count"), "prior row cluster_count"),
        "status": "blocked_unpromoted_pending_equivalent_composed_physical_activity_evidence",
        "promoted": False,
        "rankable_as_measured": False,
        "measurement_scope": "not_measured",
        "blocker": (
            "Only the directly measured c1 composed physical/activity anchor is promoted. "
            "Equivalent composed physical area and activity-backed service evidence is still required for c2+."
        ),
    }


def build_report(
    *,
    prior_cluster_frontier_json: Path,
    service_activity_power_json: Path,
) -> JsonDict:
    prior = _load(prior_cluster_frontier_json)
    service = _load(service_activity_power_json)
    (
        schedule,
        schedule_source,
        dense_qkv_tile,
        prior_c1_row,
        prior_rows,
        prior_precision,
        workload_contract,
    ) = _validated_prior_frontier(
        prior,
        prior_cluster_frontier_json,
    )
    (
        best,
        authoritative_service_ppa,
        service_window,
        activity_contract,
        workload_contract,
        macro_activity_contract,
        integrated_hashes,
    ) = _validated_service_activity(
        service,
        prior_precision,
        workload_contract,
    )
    measured = _measured_row(
        schedule=schedule,
        dense_qkv_tile=dense_qkv_tile,
        prior_c1_row=prior_c1_row,
        authoritative_service_ppa=authoritative_service_ppa,
        service_window=service_window,
        workload_contract=workload_contract,
    )
    if not measured["compute_budget_area_fit"] or not measured["timing_feasible"]:
        raise ValueError("recomputed c1 measured anchor is not feasible for promotion")
    blocked_rows = [
        _blocked_row(row)
        for row in sorted(prior_rows, key=lambda item: _positive_int(item.get("cluster_count"), "prior row cluster_count"))
        if _positive_int(row.get("cluster_count"), "prior row cluster_count") > 1
    ]
    return {
        "version": 1,
        "model": _MODEL,
        "decision": "strict_c1_measured_service_anchor_promoted_c2plus_blocked",
        "inputs": {
            "prior_cluster_frontier_json": _portable_path(prior_cluster_frontier_json),
            "service_activity_power_json": _portable_path(service_activity_power_json),
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
            "required_flow_variant": _EXPECTED_SERVICE_FLOW_VARIANT,
            "required_design": _EXPECTED_SERVICE_DESIGN,
            "required_platform": _EXPECTED_SERVICE_PLATFORM,
            "required_clock_period_ns": _EXPECTED_SERVICE_CLOCK_NS,
        },
        "schedule_contract": {
            "hidden_size": _positive_int(schedule.get("hidden_size"), "schedule hidden_size"),
            "attention_heads": _positive_int(schedule.get("attention_heads"), "schedule attention_heads"),
            "kv_heads": _positive_int(schedule.get("kv_heads"), "schedule kv_heads"),
            "layers": _positive_int(schedule.get("layers"), "schedule layers"),
            "sequence_length": _positive_int(schedule.get("sequence_length"), "schedule sequence_length"),
            "workload_contract": dict(workload_contract),
            "measured_window_active_context_tokens": measured["measured_window_active_context_tokens"],
            "measured_window_context_capacity_tokens": measured["measured_window_context_capacity_tokens"],
            "full_measured_window_count": measured["full_measured_window_count"],
            "full_measured_window_count_exact": measured["full_measured_window_count_exact"],
            "final_partial_tokens": measured["final_partial_tokens"],
            "full_head_commands_per_token": _EXPECTED_HEADS * _EXPECTED_LAYERS,
        },
        "selected_service_activity_candidate": {
            "candidate_id": _string(best.get("candidate_id"), "service best candidate_id"),
            "flow_variant": _string(best.get("flow_variant"), "service best flow_variant"),
            "integrated_service_hashes": integrated_hashes,
            "activity_contract": {
                "clock_period_ns": _positive(activity_contract.get("clock_period_ns"), "service activity clock_period_ns"),
                "cycle_count": _positive_int(activity_contract.get("cycle_count"), "service activity cycle_count"),
            },
            "activity_workload_contract": workload_contract,
            "macro_activity_contract": macro_activity_contract,
        },
        "precision": {
            "status": _EXPECTED_SERVICE_PRECISION_STATUS,
            "decision": _EXPECTED_PRIOR_PRECISION_DECISION,
            "score_tensor_hash": _string(prior_precision.get("score_tensor_hash"), "prior precision score_tensor_hash"),
            "final_tensor_hash": _string(prior_precision.get("final_tensor_hash"), "prior precision final_tensor_hash"),
            "quality_change": "none_exact_integer_semantics_preserved",
        },
        "rows": [measured, *blocked_rows],
        "promoted_rows": [measured],
        "blocked_rows": blocked_rows,
        "best_measured_anchor": measured,
        "promotion_status": (
            "strict_c1_measured_anchor_promoted_c2plus_unpromoted_pending_equivalent_"
            "composed_physical_activity_evidence"
        ),
        "remaining_abstractions": [
            "This report promotes only the directly measured c1 composed service anchor.",
            "The activity-backed energy is a microkernel-scaled composed-service component estimate, not direct total-token energy.",
            "HBM/DRAM, broader SRAM/NoC, producer, and dense-QKV activity energy remain outside this report.",
            "The 16KiB service value store remains counted inside the service instance area, while broader schedule SRAM remains separately charged.",
            "c2+ rows remain blocked until equivalent composed physical/activity evidence exists for those cluster counts.",
        ],
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    anchor = payload["best_measured_anchor"]
    lines = [
        "# Llama7B strict c1 measured-service frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promoted anchor: `{anchor['candidate_id']}`",
        f"- clock ns: `{anchor['clock_ns']}`",
        f"- latency us: `{anchor['latency_us']}`",
        f"- dense QKV tiles: `{anchor['dense_qkv_tile_count']}`",
        (
            "- area replacement: prior cluster `{prior}` mm2 -> composed service `{new}` mm2".format(
                prior=anchor["prior_cluster_area_mm2"],
                new=anchor["authoritative_composed_service_area_mm2"],
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
        "| candidate | clusters | status | promoted | rankable | latency us | area mm2 | service component mJ/token |",
        "|---|---:|---|---|---|---:|---:|---:|",
    ]
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
    parser.add_argument("--service-activity-power-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        prior_cluster_frontier_json=args.prior_cluster_frontier_json,
        service_activity_power_json=args.service_activity_power_json,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

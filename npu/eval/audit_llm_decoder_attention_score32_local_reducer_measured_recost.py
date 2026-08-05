#!/usr/bin/env python3
"""Bound the Llama7B score32 schedule with measured local-reducer evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.probe_attention_score32_exact_local_temporal_reducer_gqa8 import (  # noqa: E402
    build_report as build_local_reducer_probe_report,
)
from npu.sim.perf.attention_exact_partial import (  # noqa: E402
    FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    exact_partial_tree_service_manifest,
    finalizer_accept_interval_cycles,
    finalizer_output_latency_cycles,
)

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_local_reducer_measured_recost_v1"
_DECISION = "score32_local_reducer_measured_bounded_recost_recorded"
_EXPECTED_EXACT_REDUCTION_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_EXPECTED_FOLDED_GLOBAL_MODEL = "llm_decoder_attention_score32_folded_global_exact_reduction_recost_v2"
_EXPECTED_FOLDED_GLOBAL_DECISION = "folded_global_exact_reduction_bounded_recost_recorded"
_EXPECTED_PAIR_DESIGN = "attention_score32_exact_local_temporal_reducer_gqa8_pair_node_ng45_r7"
_EXPECTED_TEMPORAL_DESIGN = "attention_score32_exact_local_temporal_reducer_gqa8_temporal_merge_ng45_r7"
_EXPECTED_TOP_DESIGN = (
    "attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_"
    "reducer_factored_hier_folded_mersenne_macro_w8"
)
_EXPECTED_PAIR_INSTANCE_COUNT = 52
_EXPECTED_TEMPORAL_INSTANCE_COUNT = 1
_EXPECTED_CLUSTER_COUNT = 16
_EXPECTED_PRODUCERS = 53
_INHERITED_SINGLE_CLOCK_NS = 48.6509
_COMPONENT_RATE_REDUCER_GLOBAL_CLOCK_NS = 8.0
_EXPECTED_TILE_SERVICE_CYCLES = 986
_EXPECTED_QKV_CYCLES = 192
_EXPECTED_KV_WRITE_CYCLES = 10
_EXPECTED_LAYERS = 32
_EXPECTED_GQA_GROUPS = 4


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_sha256(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _row_sha256(row: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(_REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} must be {expected!r}, got {actual!r}")


def _as_float(value: Any, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be a finite number")
    return numeric


def _as_int(value: Any, label: str) -> int:
    numeric = _as_float(value, label)
    if int(numeric) != numeric:
        raise ValueError(f"{label} must be an integer")
    return int(numeric)


def _load_metrics_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _validate_exact_reduction_source(payload: JsonDict) -> dict[str, Any]:
    _require_equal(payload.get("model"), _EXPECTED_EXACT_REDUCTION_MODEL, "exact-reduction model")
    _require_equal(
        payload.get("decision"),
        "score32_exact_reduction_schedule_recost_recorded",
        "exact-reduction decision",
    )
    best_requested = payload.get("best_requested")
    if not isinstance(best_requested, dict):
        raise ValueError("exact-reduction artifact missing best_requested")
    _require_equal(best_requested.get("cross_tile_reduction_cycles"), 574, "exact-reduction reduction cycles")
    _require_equal(
        best_requested.get("replica_recost_tile_service_cycles"),
        _EXPECTED_TILE_SERVICE_CYCLES,
        "exact-reduction tile service cycles",
    )
    _require_equal(best_requested.get("replica_recost_qkv_cycles"), _EXPECTED_QKV_CYCLES, "exact-reduction qkv cycles")
    _require_equal(best_requested.get("kv_write_cycles"), _EXPECTED_KV_WRITE_CYCLES, "exact-reduction kv cycles")
    _require_equal(best_requested.get("layers"), _EXPECTED_LAYERS, "exact-reduction layers")
    _require_equal(
        _as_float(best_requested.get("replica_recost_clock_ns"), "exact-reduction clock ns"),
        _INHERITED_SINGLE_CLOCK_NS,
        "exact-reduction clock ns",
    )
    return dict(best_requested)


def _validate_folded_global_source(payload: JsonDict) -> dict[str, Any]:
    _require_equal(payload.get("model"), _EXPECTED_FOLDED_GLOBAL_MODEL, "folded-global model")
    _require_equal(payload.get("decision"), _EXPECTED_FOLDED_GLOBAL_DECISION, "folded-global decision")
    summary = payload.get("summary")
    bounds = payload.get("bounded_schedule_analysis")
    if not isinstance(summary, dict) or not isinstance(bounds, dict):
        raise ValueError("folded-global artifact missing summary/bounds")
    _require_equal(summary.get("conservative_cluster_barrier_per_group_cycles"), 4224, "folded-global barrier")
    _require_equal(summary.get("global_final_output_drain_cycles"), 2678, "folded-global global drain")
    _require_equal(
        bounds.get("strict_serialized_bound_per_group_cycles"),
        6902,
        "folded-global strict bound",
    )
    _require_equal(
        bounds.get("conditional_overlap_lower_bound_status"),
        "not_established",
        "folded-global overlap status",
    )
    return {
        "summary": dict(summary),
        "bounded_schedule_analysis": dict(bounds),
        "remaining_abstractions": list(payload.get("remaining_abstractions") or []),
    }


def _select_unique_ok_metrics_row(path: Path, *, design: str) -> dict[str, Any]:
    rows = [row for row in _load_metrics_rows(path) if row.get("design") == design and row.get("status") == "ok"]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one ok row for {design}: {path}")
    row = rows[0]
    return {
        "design": design,
        "config_hash": str(row.get("config_hash") or ""),
        "param_hash": str(row.get("param_hash") or ""),
        "tag": str(row.get("tag") or ""),
        "critical_path_ns": _as_float(row.get("critical_path_ns"), "metrics critical_path_ns"),
        "die_area_um2": _as_float(row.get("die_area"), "metrics die_area"),
        "core_area_um2": _as_float(row.get("core_area_um2"), "metrics core_area_um2"),
        "total_power_mw": _as_float(row.get("total_power_mw"), "metrics total_power_mw"),
        "flow_elapsed_seconds": _as_float(row.get("flow_elapsed_seconds"), "metrics flow_elapsed_seconds"),
        "stage_elapsed_seconds": _as_float(row.get("stage_elapsed_seconds"), "metrics stage_elapsed_seconds"),
        "result_path": str(row.get("result_path") or ""),
        "work_result_json": str(row.get("work_result_json") or ""),
        "row_sha256": _row_sha256(row),
    }


def _validate_top_config(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    body = payload.get("attention_score32_exact_local_temporal_reducer_gqa8_physical_harness")
    macro = payload.get("macro_hardening")
    if not isinstance(body, dict) or not isinstance(macro, dict):
        raise ValueError("top config missing physical harness or macro_hardening block")
    _require_equal(payload.get("top_name"), _EXPECTED_TOP_DESIGN, "top config top_name")
    _require_equal(body.get("producers"), _EXPECTED_PRODUCERS, "top config producers")
    _require_equal(body.get("mode"), "reducer", "top config mode")
    _require_equal(body.get("waves"), 8, "top config waves")
    _require_equal(
        body.get("pair_node_impl"),
        FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
        "top config pair_node_impl",
    )
    _require_equal(body.get("exp_scale_impl"), "factored_h33_l64_mul_exact", "top config exp_scale_impl")
    _require_equal(macro.get("pair_node_macro_id"), _EXPECTED_PAIR_DESIGN, "top config pair macro id")
    _require_equal(
        macro.get("temporal_merge_macro_id"),
        _EXPECTED_TEMPORAL_DESIGN,
        "top config temporal macro id",
    )
    bundle = macro.get("bundle_manifest_params")
    if not isinstance(bundle, dict):
        raise ValueError("top config missing bundle_manifest_params")
    _require_equal(bundle.get("pair_node_instance_count"), _EXPECTED_PAIR_INSTANCE_COUNT, "pair instance count")
    _require_equal(
        bundle.get("temporal_merge_instance_count"),
        _EXPECTED_TEMPORAL_INSTANCE_COUNT,
        "temporal instance count",
    )
    return payload


def _validate_r6_diagnostic(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    hierarchy = payload.get("hierarchy_evidence")
    service = payload.get("measured_service_evidence")
    if not isinstance(hierarchy, dict) or not isinstance(service, dict):
        raise ValueError("r6 diagnostic missing hierarchy or measured service evidence")
    _require_equal(hierarchy.get("local_pair_node_instances"), _EXPECTED_PAIR_INSTANCE_COUNT, "r6 pair instances")
    _require_equal(hierarchy.get("temporal_merge_instances"), _EXPECTED_TEMPORAL_INSTANCE_COUNT, "r6 temporal instances")
    _require_equal(service.get("conservative_producer_barrier_cycles_per_group"), 4224, "r6 producer barrier")
    return payload


def _validate_macro_top_failures(path: Path) -> dict[str, Any]:
    rows = [row for row in _load_metrics_rows(path) if row.get("design") == _EXPECTED_TOP_DESIGN]
    if len(rows) != 2:
        raise ValueError(f"expected exactly two failure rows in {path}")
    by_clock = {round(_as_float(row.get("params_json", "").split('"CLOCK_PERIOD": ')[1].split(",")[0], "clock"), 1): row for row in rows}
    ten = by_clock.get(10.0)
    fifteen = by_clock.get(15.0)
    if ten is None or fifteen is None:
        raise ValueError("expected 10ns and 15ns rows in macro-top metrics")
    for row in (ten, fifteen):
        _require_equal(row.get("status"), "flow_failed", "macro-top status")
        _require_equal(row.get("config_hash"), "c8892c493f64", "macro-top config_hash")
    ten_row = {
        "clock_period_ns": 10.0,
        "param_hash": str(ten["param_hash"]),
        "core_area_um2": _as_float(ten.get("core_area_um2"), "10ns core_area_um2"),
        "failure_signature": str(ten.get("failure_signature") or ""),
        "failure_log_path": str(ten.get("failure_log_path") or ""),
        "row_sha256": _row_sha256(ten),
        "classification": "global_route_oom_boundary",
    }
    if not ten_row["failure_log_path"].endswith("/5_1_grt.log"):
        raise ValueError("10ns failure must point at 5_1_grt.log")
    fifteen_row = {
        "clock_period_ns": 15.0,
        "param_hash": str(fifteen["param_hash"]),
        "core_area_um2": _as_float(fifteen.get("core_area_um2"), "15ns core_area_um2"),
        "failure_signature": str(fifteen.get("failure_signature") or ""),
        "failure_log_path": str(fifteen.get("failure_log_path") or ""),
        "row_sha256": _row_sha256(fifteen),
        "classification": "macro_placer_assertion",
    }
    if not fifteen_row["failure_log_path"].endswith("/2_2_floorplan_macro.log"):
        raise ValueError("15ns failure must point at 2_2_floorplan_macro.log")
    return {"10ns": ten_row, "15ns": fifteen_row}


def _build_folded_probe_config(config_payload: JsonDict) -> JsonDict:
    cloned = json.loads(json.dumps(config_payload))
    body = cloned["attention_score32_exact_local_temporal_reducer_gqa8"]
    body["pair_node_impl"] = FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL
    body["exp_scale_impl"] = "factored_h33_l64_mul_exact"
    return cloned


def _measure_local_reducer_service(config_payload: JsonDict) -> dict[str, Any]:
    folded_config = _build_folded_probe_config(config_payload)
    report = build_local_reducer_probe_report(
        folded_config,
        heads=8,
        command_count=1,
        head_bases=(0,),
    )
    if not bool(report.get("passed")):
        raise ValueError("local reducer probe must pass")
    _require_equal(report.get("drain_cycles"), 20730, "local reducer drain_cycles")
    _require_equal(report.get("local_root_completed_count"), 1024, "local reducer local_root_completed_count")
    _require_equal(report.get("temporal_merge_completed_count"), 896, "local reducer temporal_merge_completed_count")
    _require_equal(report.get("completed_command_count"), 1, "local reducer completed_command_count")
    service_model = report.get("service_model")
    if not isinstance(service_model, dict):
        raise ValueError("local reducer probe missing service_model")
    _require_equal(
        service_model.get("comparison_cycle_origin"),
        "cycle0_on_first_leaf_issue_of_group0_wave0",
        "local reducer comparison_cycle_origin",
    )
    return {
        "probe_overrides": {
            "heads": 8,
            "command_count": 1,
            "head_bases": [0],
            "pair_node_impl": FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
            "exp_scale_impl": "factored_h33_l64_mul_exact",
        },
        "runtime_config_canonical_sha256": _canonical_json_sha256(folded_config),
        "measured_report": {
            "drain_cycles": int(report["drain_cycles"]),
            "first_output_cycle": int(report["observed_cycles"][0]),
            "last_output_cycle": int(report["observed_cycles"][-1]),
            "outputs": int(report["outputs"]),
            "local_root_completed_count": int(report["local_root_completed_count"]),
            "temporal_merge_completed_count": int(report["temporal_merge_completed_count"]),
            "completed_command_count": int(report["completed_command_count"]),
        },
        "service_model": service_model,
        "semantic_scope": {
            "includes_producer_compute_or_service": False,
            "measurement_scope": "reducer_only_ideal_precomputed_leaf_partials",
            "explanation": (
                "The p53 folded probe starts at the first precomputed leaf-partial issue and measures only the "
                "local temporal reducer under ideal input service; producer compute/service remains outside this window."
            ),
        },
        "source_identities": dict(report.get("source_identities") or {}),
    }


def _derive_global_tree_finalizer_contract() -> dict[str, Any]:
    service = exact_partial_tree_service_manifest(
        clusters=16,
        heads=8,
        pair_node_impl=FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    )
    _require_equal(service.get("full_wave_last_root_output_cycle"), 2620, "global tree last root output cycle")
    output_latency = finalizer_output_latency_cycles(8)
    accept_interval = finalizer_accept_interval_cycles(8)
    composed_drain = int(service["full_wave_last_root_output_cycle"]) + output_latency
    _require_equal(output_latency, 58, "finalizer output latency")
    _require_equal(accept_interval, 59, "finalizer accept interval")
    _require_equal(composed_drain, 2678, "global tree/finalizer drain")
    return {
        "service": service,
        "per_bank_output_latency_cycles": output_latency,
        "per_bank_accept_interval_cycles": accept_interval,
        "composed_global_final_output_drain_cycles": composed_drain,
    }


def _sum_macro_ppa(pair_row: dict[str, Any], temporal_row: dict[str, Any]) -> dict[str, Any]:
    pair_instances = _EXPECTED_PAIR_INSTANCE_COUNT
    temporal_instances = _EXPECTED_TEMPORAL_INSTANCE_COUNT
    die_area = (pair_instances * pair_row["die_area_um2"]) + (temporal_instances * temporal_row["die_area_um2"])
    core_area = (pair_instances * pair_row["core_area_um2"]) + (temporal_instances * temporal_row["core_area_um2"])
    power = (pair_instances * pair_row["total_power_mw"]) + (temporal_instances * temporal_row["total_power_mw"])
    return {
        "pair_node_instances": pair_instances,
        "temporal_merge_instances": temporal_instances,
        "max_component_critical_path_ns": max(pair_row["critical_path_ns"], temporal_row["critical_path_ns"]),
        "die_area_um2": die_area,
        "core_area_um2": core_area,
        "total_power_mw": power,
        "die_area_mm2": round(die_area / 1_000_000.0, 6),
        "core_area_mm2": round(core_area / 1_000_000.0, 6),
    }


def _scale_cluster_scope(payload: dict[str, Any], *, clusters: int) -> dict[str, Any]:
    scaled = {}
    for key, value in payload.items():
        if key.endswith("_um2") or key.endswith("_mw") or key.endswith("_count"):
            scaled[key] = value * clusters
        else:
            scaled[key] = value
    if "die_area_um2" in scaled:
        scaled["die_area_mm2"] = round(scaled["die_area_um2"] / 1_000_000.0, 6)
    if "core_area_um2" in scaled:
        scaled["core_area_mm2"] = round(scaled["core_area_um2"] / 1_000_000.0, 6)
    if "top_logic_area_um2_excluding_submodules" in scaled:
        scaled["top_logic_area_mm2_excluding_submodules"] = round(
            scaled["top_logic_area_um2_excluding_submodules"] / 1_000_000.0, 6
        )
    if "total_hierarchy_area_um2" in scaled:
        scaled["total_hierarchy_area_mm2"] = round(scaled["total_hierarchy_area_um2"] / 1_000_000.0, 6)
    return scaled


def build_report(args: argparse.Namespace) -> JsonDict:
    exact_reduction_path = Path(args.exact_reduction_json).resolve()
    folded_global_path = Path(args.folded_global_json).resolve()
    pair_metrics_path = Path(args.pair_metrics).resolve()
    temporal_metrics_path = Path(args.temporal_metrics).resolve()
    macro_top_metrics_path = Path(args.macro_top_metrics).resolve()
    r6_diagnostic_path = Path(args.r6_diagnostic_json).resolve()
    probe_config_path = Path(args.reducer_probe_config).resolve()
    top_config_path = Path(args.macro_top_config).resolve()

    exact_reduction_payload = _load_json(exact_reduction_path)
    folded_global_payload = _load_json(folded_global_path)
    source_best_requested = _validate_exact_reduction_source(exact_reduction_payload)
    folded_global = _validate_folded_global_source(folded_global_payload)
    pair_row = _select_unique_ok_metrics_row(pair_metrics_path, design=_EXPECTED_PAIR_DESIGN)
    temporal_row = _select_unique_ok_metrics_row(temporal_metrics_path, design=_EXPECTED_TEMPORAL_DESIGN)
    top_config_payload = _validate_top_config(top_config_path)
    r6_diagnostic = _validate_r6_diagnostic(r6_diagnostic_path)
    macro_top_failures = _validate_macro_top_failures(macro_top_metrics_path)
    probe_config_payload = _load_json(probe_config_path)
    local_reducer_service = _measure_local_reducer_service(probe_config_payload)
    global_tree = _derive_global_tree_finalizer_contract()

    producer_barrier_cycles = int(r6_diagnostic["measured_service_evidence"]["conservative_producer_barrier_cycles_per_group"])
    local_reducer_cycles = int(local_reducer_service["measured_report"]["drain_cycles"])
    global_tree_cycles = int(global_tree["composed_global_final_output_drain_cycles"])
    strict_no_overlap_per_group_cycles = producer_barrier_cycles + local_reducer_cycles + global_tree_cycles
    conditional_overlap_per_group_cycles = max(producer_barrier_cycles, local_reducer_cycles) + global_tree_cycles

    strict_single_clock_attention_tail_cycles = _EXPECTED_GQA_GROUPS * strict_no_overlap_per_group_cycles
    conditional_single_clock_attention_tail_cycles = _EXPECTED_GQA_GROUPS * conditional_overlap_per_group_cycles

    strict_single_clock_layer_cycles = (
        _EXPECTED_QKV_CYCLES + _EXPECTED_KV_WRITE_CYCLES + strict_single_clock_attention_tail_cycles
    )
    strict_single_clock_total_cycles = _EXPECTED_LAYERS * strict_single_clock_layer_cycles
    strict_single_clock_latency_us = round(
        (strict_single_clock_total_cycles * _INHERITED_SINGLE_CLOCK_NS) / 1000.0,
        6,
    )
    strict_single_clock_throughput = round(1_000_000.0 / strict_single_clock_latency_us, 12)

    conditional_single_clock_layer_cycles = (
        _EXPECTED_QKV_CYCLES + _EXPECTED_KV_WRITE_CYCLES + conditional_single_clock_attention_tail_cycles
    )
    conditional_single_clock_total_cycles = _EXPECTED_LAYERS * conditional_single_clock_layer_cycles
    conditional_single_clock_latency_us = round(
        (conditional_single_clock_total_cycles * _INHERITED_SINGLE_CLOCK_NS) / 1000.0,
        6,
    )
    conditional_single_clock_throughput = round(1_000_000.0 / conditional_single_clock_latency_us, 12)

    qkv_kv_single_clock_time_ns = (_EXPECTED_QKV_CYCLES + _EXPECTED_KV_WRITE_CYCLES) * _INHERITED_SINGLE_CLOCK_NS
    producer_group_time_ns = producer_barrier_cycles * _INHERITED_SINGLE_CLOCK_NS
    local_reducer_group_time_ns = local_reducer_cycles * _COMPONENT_RATE_REDUCER_GLOBAL_CLOCK_NS
    global_tree_group_time_ns = global_tree_cycles * _COMPONENT_RATE_REDUCER_GLOBAL_CLOCK_NS
    strict_dual_clock_group_time_ns = producer_group_time_ns + local_reducer_group_time_ns + global_tree_group_time_ns
    conditional_dual_clock_group_time_ns = max(producer_group_time_ns, local_reducer_group_time_ns) + global_tree_group_time_ns
    strict_dual_clock_layer_time_ns = qkv_kv_single_clock_time_ns + (_EXPECTED_GQA_GROUPS * strict_dual_clock_group_time_ns)
    conditional_dual_clock_layer_time_ns = (
        qkv_kv_single_clock_time_ns + (_EXPECTED_GQA_GROUPS * conditional_dual_clock_group_time_ns)
    )
    strict_dual_clock_total_latency_us = round((strict_dual_clock_layer_time_ns * _EXPECTED_LAYERS) / 1000.0, 6)
    conditional_dual_clock_total_latency_us = round(
        (conditional_dual_clock_layer_time_ns * _EXPECTED_LAYERS) / 1000.0,
        6,
    )
    strict_dual_clock_throughput = round(1_000_000.0 / strict_dual_clock_total_latency_us, 12)
    conditional_dual_clock_throughput = round(1_000_000.0 / conditional_dual_clock_total_latency_us, 12)

    source_latency_us = _as_float(source_best_requested["replica_recost_latency_us"], "source replica_recost_latency_us")
    source_schedule_latency_us = _as_float(source_best_requested["source_latency_us"], "source source_latency_us")

    corrected_best_requested = dict(source_best_requested)
    corrected_best_requested.update(
        {
            "cross_tile_reduction_cycles": strict_single_clock_attention_tail_cycles,
            "base_cross_tile_reduction_cycles": strict_single_clock_attention_tail_cycles,
            "replica_recost_tile_service_cycles": 0,
            "tile_service_cycles": 0,
            "historical_tile_service_cycles_per_group_source": _EXPECTED_TILE_SERVICE_CYCLES,
            "replica_recost_layer_cycles": strict_single_clock_layer_cycles,
            "layer_cycles": strict_single_clock_layer_cycles,
            "replica_recost_total_cycles": strict_single_clock_total_cycles,
            "total_cycles": strict_single_clock_total_cycles,
            "replica_recost_clock_ns": _INHERITED_SINGLE_CLOCK_NS,
            "replica_recost_clock_origin": "inherited_single_clock_composed_compute_bound",
            "replica_recost_latency_us": strict_single_clock_latency_us,
            "adjusted_latency_us_if_feasible": strict_single_clock_latency_us,
            "replica_recost_latency_slowdown_vs_source": round(strict_single_clock_latency_us / source_latency_us, 12),
            "adjusted_speedup_if_feasible": round(source_schedule_latency_us / strict_single_clock_latency_us, 12),
            "token_throughput_per_s": strict_single_clock_throughput,
            "token_throughput_bound_type": "lower_bound_single_clock_no_overlap",
            "gqa_groups_per_layer": _EXPECTED_GQA_GROUPS,
            "producer_barrier_cycles_per_group": producer_barrier_cycles,
            "local_reducer_cycles_per_group": local_reducer_cycles,
            "global_tree_cycles_per_group": global_tree_cycles,
            "local_reducer_measured_recost_replaces_unresolved_local_reducer_timing": True,
        }
    )

    macro_only_per_cluster = _sum_macro_ppa(pair_row, temporal_row)
    hierarchy = dict(r6_diagnostic["hierarchy_evidence"])
    macro_only_scaled_16 = _scale_cluster_scope(
        {
            "die_area_um2": macro_only_per_cluster["die_area_um2"],
            "core_area_um2": macro_only_per_cluster["core_area_um2"],
            "total_power_mw": macro_only_per_cluster["total_power_mw"],
        },
        clusters=_EXPECTED_CLUSTER_COUNT,
    )
    hierarchy_scaled_16 = _scale_cluster_scope(
        {
            "top_logic_stdcell_count_excluding_submodules": int(hierarchy["top_logic_stdcell_count_excluding_submodules"]),
            "top_logic_area_um2_excluding_submodules": float(hierarchy["top_logic_area_um2_excluding_submodules"]),
            "total_hierarchy_stdcell_count": int(hierarchy["total_hierarchy_stdcell_count"]),
            "total_hierarchy_area_um2": float(hierarchy["total_hierarchy_area_um2"]),
        },
        clusters=_EXPECTED_CLUSTER_COUNT,
    )

    return {
        "version": 1,
        "model": _MODEL,
        "decision": _DECISION,
        "quality_rerun_required": False,
        "quality_rerun_reason": "Exact score32 reducer semantics are unchanged; this artifact replaces only timing/PPA interpretation.",
        "source_revision": {
            "primary_schedule_source_item_id": "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1_r2",
            "primary_schedule_source_model": _EXPECTED_EXACT_REDUCTION_MODEL,
            "intermediate_bounded_source_item_id": "l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2",
            "intermediate_bounded_source_model": _EXPECTED_FOLDED_GLOBAL_MODEL,
            "source_best_requested_preserved": True,
            "local_reducer_timing_replaced_only": True,
            "routed_composed_top_ppa_claimed": False,
        },
        "source_artifacts": {
            "exact_reduction_json": {
                "path": _portable_path(exact_reduction_path),
                "file_sha256": _sha256_file(exact_reduction_path),
                "canonical_json_sha256": _canonical_json_sha256(exact_reduction_payload),
            },
            "folded_global_json": {
                "path": _portable_path(folded_global_path),
                "file_sha256": _sha256_file(folded_global_path),
                "canonical_json_sha256": _canonical_json_sha256(folded_global_payload),
            },
            "pair_metrics_csv": {
                "path": _portable_path(pair_metrics_path),
                "file_sha256": _sha256_file(pair_metrics_path),
                "selected_row_sha256": pair_row["row_sha256"],
            },
            "temporal_metrics_csv": {
                "path": _portable_path(temporal_metrics_path),
                "file_sha256": _sha256_file(temporal_metrics_path),
                "selected_row_sha256": temporal_row["row_sha256"],
            },
            "macro_top_metrics_csv": {
                "path": _portable_path(macro_top_metrics_path),
                "file_sha256": _sha256_file(macro_top_metrics_path),
                "failure_row_sha256": {
                    "10ns": macro_top_failures["10ns"]["row_sha256"],
                    "15ns": macro_top_failures["15ns"]["row_sha256"],
                },
            },
            "r6_diagnostic_json": {
                "path": _portable_path(r6_diagnostic_path),
                "file_sha256": _sha256_file(r6_diagnostic_path),
                "canonical_json_sha256": _canonical_json_sha256(r6_diagnostic),
            },
            "reducer_probe_config_json": {
                "path": _portable_path(probe_config_path),
                "file_sha256": _sha256_file(probe_config_path),
                "canonical_json_sha256": _canonical_json_sha256(probe_config_payload),
            },
            "macro_top_config_json": {
                "path": _portable_path(top_config_path),
                "file_sha256": _sha256_file(top_config_path),
                "canonical_json_sha256": _canonical_json_sha256(top_config_payload),
            },
            "probe_script_py": {
                "path": "npu/eval/probe_attention_score32_exact_local_temporal_reducer_gqa8.py",
                "file_sha256": _sha256_file(_REPO_ROOT / "npu/eval/probe_attention_score32_exact_local_temporal_reducer_gqa8.py"),
            },
            "exact_partial_module_py": {
                "path": "npu/sim/perf/attention_exact_partial.py",
                "file_sha256": _sha256_file(_REPO_ROOT / "npu/sim/perf/attention_exact_partial.py"),
            },
        },
        "identity_validation": {
            "pair_macro_design": pair_row["design"],
            "temporal_macro_design": temporal_row["design"],
            "top_design": _EXPECTED_TOP_DESIGN,
            "pair_instance_count": _EXPECTED_PAIR_INSTANCE_COUNT,
            "temporal_instance_count": _EXPECTED_TEMPORAL_INSTANCE_COUNT,
            "config_pair_macro_id": top_config_payload["macro_hardening"]["pair_node_macro_id"],
            "config_temporal_macro_id": top_config_payload["macro_hardening"]["temporal_merge_macro_id"],
            "hierarchy_counts_match_r6_diagnostic": True,
        },
        "routed_component_ppa": {
            "pair_node": pair_row,
            "temporal_merge": temporal_row,
            "macro_only_sum_per_cluster": macro_only_per_cluster,
            "macro_only_sum_scaled_16_clusters": macro_only_scaled_16,
            "synthesis_area_lower_bound_per_cluster": {
                "top_logic_stdcell_count_excluding_submodules": int(hierarchy["top_logic_stdcell_count_excluding_submodules"]),
                "top_logic_area_um2_excluding_submodules": float(hierarchy["top_logic_area_um2_excluding_submodules"]),
                "top_logic_area_mm2_excluding_submodules": round(
                    float(hierarchy["top_logic_area_um2_excluding_submodules"]) / 1_000_000.0, 6
                ),
                "total_hierarchy_stdcell_count": int(hierarchy["total_hierarchy_stdcell_count"]),
                "total_hierarchy_area_um2": float(hierarchy["total_hierarchy_area_um2"]),
                "total_hierarchy_area_mm2": round(float(hierarchy["total_hierarchy_area_um2"]) / 1_000_000.0, 6),
            },
            "synthesis_area_lower_bound_scaled_16_clusters": hierarchy_scaled_16,
            "composed_top_route_claim": "absent",
        },
        "macro_top_boundary_failures": {
            "10ns": {
                **macro_top_failures["10ns"],
                "note": "Macro-composed p53 top reached global routing and then failed under boundary-class memory pressure; no routed top PPA row exists.",
            },
            "15ns": {
                **macro_top_failures["15ns"],
                "note": "Macro placer asserted during floorplan macro placement; this is a placement-tool boundary, not a timing-feasible routed top result.",
            },
        },
        "local_reducer_service_evidence": local_reducer_service,
        "global_tree_finalizer_contract": global_tree,
        "schedule_recost": {
            "source_exact_reduction_contract": {
                "cross_tile_reduction_cycles": int(source_best_requested["cross_tile_reduction_cycles"]),
                "replica_recost_tile_service_cycles": int(source_best_requested["replica_recost_tile_service_cycles"]),
                "replica_recost_layer_cycles": int(source_best_requested["replica_recost_layer_cycles"]),
                "replica_recost_total_cycles": int(source_best_requested["replica_recost_total_cycles"]),
                "replica_recost_latency_us": source_latency_us,
                "source_latency_us": source_schedule_latency_us,
                "replica_recost_clock_ns": _as_float(
                    source_best_requested["replica_recost_clock_ns"],
                    "source replica_recost_clock_ns",
                ),
                "token_throughput_per_s": _as_float(source_best_requested["token_throughput_per_s"], "source throughput"),
            },
            "previous_bounded_interpretation": {
                "strict_serialized_bound_per_group_cycles": int(
                    folded_global["bounded_schedule_analysis"]["strict_serialized_bound_per_group_cycles"]
                ),
                "components": {
                    "conservative_producer_barrier_cycles_per_group": int(
                        folded_global["summary"]["conservative_cluster_barrier_per_group_cycles"]
                    ),
                    "global_tree_finalizer_cycles": int(folded_global["summary"]["global_final_output_drain_cycles"]),
                    "local_reducer_cycles": "unresolved",
                },
            },
            "corrected_bounded_schedule": {
                "strict_no_overlap_per_group_cycles": strict_no_overlap_per_group_cycles,
                "strict_no_overlap_formula": "4224(producer barrier) + 20730(local reducer) + 2678(global tree/finalizer)",
                "conditional_overlap_lower_bound_per_group_cycles": conditional_overlap_per_group_cycles,
                "conditional_overlap_formula": "max(4224 producer barrier, 20730 reducer-only ideal-input service) + 2678 global tree/finalizer",
                "conditional_overlap_status": "not_measured_composition",
                "conditional_overlap_note": (
                    "The overlap lower bound assumes producer service can overlap with reducer collection because the "
                    "20730-cycle probe starts at first leaf issue and excludes producer compute/service. This is not a measured full composition."
                ),
            },
            "single_clock_full_layer_bound": {
                "clock_ns": _INHERITED_SINGLE_CLOCK_NS,
                "clock_origin": "inherited_single_clock_composed_compute_bound",
                "gqa_groups_per_layer": _EXPECTED_GQA_GROUPS,
                "producer_barrier_already_includes_all_8_waves_per_group": True,
                "historical_tile_service_cycles_per_group_not_added": _EXPECTED_TILE_SERVICE_CYCLES,
                "replica_recost_qkv_cycles": _EXPECTED_QKV_CYCLES,
                "kv_write_cycles": _EXPECTED_KV_WRITE_CYCLES,
                "strict_no_overlap_attention_tail_cycles": strict_single_clock_attention_tail_cycles,
                "strict_no_overlap_layer_cycles": strict_single_clock_layer_cycles,
                "strict_no_overlap_total_cycles": strict_single_clock_total_cycles,
                "strict_no_overlap_latency_upper_bound_us": strict_single_clock_latency_us,
                "strict_no_overlap_throughput_lower_bound_per_s": strict_single_clock_throughput,
                "conditional_overlap_attention_tail_cycles": conditional_single_clock_attention_tail_cycles,
                "conditional_overlap_layer_cycles": conditional_single_clock_layer_cycles,
                "conditional_overlap_total_cycles": conditional_single_clock_total_cycles,
                "conditional_overlap_latency_lower_bound_us": conditional_single_clock_latency_us,
                "conditional_overlap_throughput_upper_bound_per_s": conditional_single_clock_throughput,
            },
            "dual_clock_component_rate_bound": {
                "producer_clock_ns": _INHERITED_SINGLE_CLOCK_NS,
                "reducer_global_clock_ns": _COMPONENT_RATE_REDUCER_GLOBAL_CLOCK_NS,
                "cdc_handshake_required": True,
                "measured_full_composition": False,
                "gqa_groups_per_layer": _EXPECTED_GQA_GROUPS,
                "qkv_kv_single_clock_time_ns_per_layer": qkv_kv_single_clock_time_ns,
                "strict_no_overlap_group_time_ns": strict_dual_clock_group_time_ns,
                "strict_no_overlap_formula": (
                    "4224*48.6509ns + 20730*8.0ns + 2678*8.0ns per group, plus (192+10)*48.6509ns once per layer"
                ),
                "strict_no_overlap_latency_upper_bound_us": strict_dual_clock_total_latency_us,
                "strict_no_overlap_throughput_lower_bound_per_s": strict_dual_clock_throughput,
                "conditional_overlap_group_time_ns": conditional_dual_clock_group_time_ns,
                "conditional_overlap_formula": (
                    "max(4224*48.6509ns, 20730*8.0ns) + 2678*8.0ns per group, plus (192+10)*48.6509ns once per layer"
                ),
                "conditional_overlap_latency_lower_bound_us": conditional_dual_clock_total_latency_us,
                "conditional_overlap_throughput_upper_bound_per_s": conditional_dual_clock_throughput,
            },
        },
        "best_requested": corrected_best_requested,
        "delta_vs_source": {
            "cross_tile_reduction_cycles": strict_single_clock_attention_tail_cycles
            - int(source_best_requested["cross_tile_reduction_cycles"]),
            "replica_recost_layer_cycles": strict_single_clock_layer_cycles
            - int(source_best_requested["replica_recost_layer_cycles"]),
            "replica_recost_total_cycles": strict_single_clock_total_cycles
            - int(source_best_requested["replica_recost_total_cycles"]),
            "replica_recost_latency_us": round(strict_single_clock_latency_us - source_latency_us, 12),
            "adjusted_latency_us_if_feasible": round(
                strict_single_clock_latency_us
                - _as_float(
                    source_best_requested["adjusted_latency_us_if_feasible"],
                    "source adjusted_latency_us_if_feasible",
                ),
                12,
            ),
            "token_throughput_per_s": round(
                strict_single_clock_throughput
                - _as_float(source_best_requested["token_throughput_per_s"], "source throughput"),
                12,
            ),
        },
        "remaining_abstractions": [
            "The routed composed p53 top still has only boundary evidence; no routed top-level PPA row exists.",
            "The 16-cluster scaling is arithmetic replication of measured/derived per-cluster evidence and is not a routed full-array composition.",
            "The single-clock bound inherits the 48.6509ns composed-compute clock from the earlier score32 artifact and should not be read as the standalone reducer clock.",
            "The dual-clock component-rate bounds require CDC plus a proved scheduler/handshake implementation and are not measured full compositions.",
            "No quality delta is claimed; this artifact changes timing/PPA interpretation only.",
            "No 328-bit transport, NoC, SRAM, or local-reducer activity-power closure is claimed here.",
        ],
        "summary": {
            "source_strict_bound_per_group_cycles": int(
                folded_global["bounded_schedule_analysis"]["strict_serialized_bound_per_group_cycles"]
            ),
            "corrected_strict_no_overlap_per_group_cycles": strict_no_overlap_per_group_cycles,
            "conditional_overlap_lower_bound_per_group_cycles": conditional_overlap_per_group_cycles,
            "single_clock_strict_latency_upper_bound_us": strict_single_clock_latency_us,
            "single_clock_strict_throughput_lower_bound_per_s": strict_single_clock_throughput,
            "single_clock_conditional_latency_lower_bound_us": conditional_single_clock_latency_us,
            "single_clock_conditional_throughput_upper_bound_per_s": conditional_single_clock_throughput,
            "dual_clock_strict_latency_upper_bound_us": strict_dual_clock_total_latency_us,
            "dual_clock_strict_throughput_lower_bound_per_s": strict_dual_clock_throughput,
            "dual_clock_conditional_latency_lower_bound_us": conditional_dual_clock_total_latency_us,
            "dual_clock_conditional_throughput_upper_bound_per_s": conditional_dual_clock_throughput,
            "macro_only_area_mm2_per_cluster": macro_only_per_cluster["die_area_mm2"],
            "macro_only_area_mm2_scaled_16_clusters": macro_only_scaled_16["die_area_mm2"],
            "synthesis_area_lower_bound_mm2_per_cluster": round(float(hierarchy["total_hierarchy_area_um2"]) / 1_000_000.0, 6),
            "synthesis_area_lower_bound_mm2_scaled_16_clusters": hierarchy_scaled_16["total_hierarchy_area_mm2"],
        },
    }


def _build_markdown(report: JsonDict) -> str:
    pair = report["routed_component_ppa"]["pair_node"]
    temporal = report["routed_component_ppa"]["temporal_merge"]
    macro_sum = report["routed_component_ppa"]["macro_only_sum_per_cluster"]
    synth = report["routed_component_ppa"]["synthesis_area_lower_bound_per_cluster"]
    schedule = report["schedule_recost"]
    source = schedule["source_exact_reduction_contract"]
    single_clock = schedule["single_clock_full_layer_bound"]
    dual_clock = schedule["dual_clock_component_rate_bound"]
    lines = [
        "# Score32 Local Reducer Measured Recost",
        "",
        f"- decision: `{report['decision']}`",
        f"- exact-reduction source: `{report['source_artifacts']['exact_reduction_json']['path']}`",
        f"- bounded global source: `{report['source_artifacts']['folded_global_json']['path']}`",
        f"- reducer probe config: `{report['source_artifacts']['reducer_probe_config_json']['path']}`",
        f"- quality rerun required: `{str(report['quality_rerun_required']).lower()}`",
        "",
        "## Routed Components",
        "",
        "| component | critical path ns | die area um2 | core area um2 | power mW |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| pair node | {pair['critical_path_ns']:.4f} | {pair['die_area_um2']:.1f} | {pair['core_area_um2']:.1f} | {pair['total_power_mw']:.2f} |",
        f"| temporal merge | {temporal['critical_path_ns']:.4f} | {temporal['die_area_um2']:.1f} | {temporal['core_area_um2']:.1f} | {temporal['total_power_mw']:.2f} |",
        f"| macro-only sum per cluster (52 pair + 1 temporal) | {macro_sum['max_component_critical_path_ns']:.4f} | {macro_sum['die_area_um2']:.1f} | {macro_sum['core_area_um2']:.1f} | {macro_sum['total_power_mw']:.2f} |",
        "",
        "No routed composed-top PPA claim is made.",
        "",
        "## Area Bounds",
        "",
        f"- synthesis-area lower bound per cluster: `{synth['total_hierarchy_area_mm2']:.6f}` mm2 (`{synth['total_hierarchy_stdcell_count']}` cells)",
        f"- top logic excluding submodules per cluster: `{synth['top_logic_area_mm2_excluding_submodules']:.6f}` mm2 (`{synth['top_logic_stdcell_count_excluding_submodules']}` cells)",
        f"- macro-only die-area sum per cluster: `{macro_sum['die_area_mm2']:.6f}` mm2",
        f"- macro-only die-area sum scaled to 16 clusters: `{report['routed_component_ppa']['macro_only_sum_scaled_16_clusters']['die_area_mm2']:.6f}` mm2",
        f"- synthesis-area lower bound scaled to 16 clusters: `{report['routed_component_ppa']['synthesis_area_lower_bound_scaled_16_clusters']['total_hierarchy_area_mm2']:.6f}` mm2",
        "",
        "## Boundary Failures",
        "",
        f"- 10ns: `{report['macro_top_boundary_failures']['10ns']['classification']}` via `{report['macro_top_boundary_failures']['10ns']['failure_log_path']}`",
        f"- 15ns: `{report['macro_top_boundary_failures']['15ns']['classification']}` via `{report['macro_top_boundary_failures']['15ns']['failure_log_path']}`",
        "",
        "## Service Scope",
        "",
        f"- reducer-only drain cycles: `{report['local_reducer_service_evidence']['measured_report']['drain_cycles']}`",
        f"- first output cycle: `{report['local_reducer_service_evidence']['measured_report']['first_output_cycle']}`",
        f"- last output cycle: `{report['local_reducer_service_evidence']['measured_report']['last_output_cycle']}`",
        f"- comparison cycle origin: `{report['local_reducer_service_evidence']['service_model']['comparison_cycle_origin']}`",
        f"- includes producer compute/service: `{str(report['local_reducer_service_evidence']['semantic_scope']['includes_producer_compute_or_service']).lower()}`",
        "",
        "## Single-Clock Bound",
        "",
        "| schedule term | source exact-reduction | strict no-overlap | conditional overlap |",
        "| --- | ---: | ---: | ---: |",
        f"| per-group reduction cycles | {source['cross_tile_reduction_cycles']} | {schedule['corrected_bounded_schedule']['strict_no_overlap_per_group_cycles']} | {schedule['corrected_bounded_schedule']['conditional_overlap_lower_bound_per_group_cycles']} |",
        f"| full-layer attention-tail cycles | {source['cross_tile_reduction_cycles']} | {single_clock['strict_no_overlap_attention_tail_cycles']} | {single_clock['conditional_overlap_attention_tail_cycles']} |",
        f"| layer cycles | {source['replica_recost_layer_cycles']} | {single_clock['strict_no_overlap_layer_cycles']} | {single_clock['conditional_overlap_layer_cycles']} |",
        f"| total cycles | {source['replica_recost_total_cycles']} | {single_clock['strict_no_overlap_total_cycles']} | {single_clock['conditional_overlap_total_cycles']} |",
        f"| latency us | {source['replica_recost_latency_us']:.6f} | {single_clock['strict_no_overlap_latency_upper_bound_us']:.6f} | {single_clock['conditional_overlap_latency_lower_bound_us']:.6f} |",
        f"| token/s | {source['token_throughput_per_s']:.12f} | {single_clock['strict_no_overlap_throughput_lower_bound_per_s']:.12f} | {single_clock['conditional_overlap_throughput_upper_bound_per_s']:.12f} |",
        "",
        f"- inherited single-clock bound: `{single_clock['clock_ns']}` ns",
        f"- inherited clock origin: `{single_clock['clock_origin']}`",
        f"- producer barrier already includes all 8 producer waves per group: `{str(single_clock['producer_barrier_already_includes_all_8_waves_per_group']).lower()}`",
        f"- historical tile-service term not added separately: `{single_clock['historical_tile_service_cycles_per_group_not_added']}` cycles per group",
        "",
        "## Dual-Clock Component-Rate Bound",
        "",
        f"- producer clock: `{dual_clock['producer_clock_ns']}` ns",
        f"- reducer/global clock: `{dual_clock['reducer_global_clock_ns']}` ns",
        f"- CDC/handshake required: `{str(dual_clock['cdc_handshake_required']).lower()}`",
        f"- measured full composition: `{str(dual_clock['measured_full_composition']).lower()}`",
        f"- strict no-overlap group time: `{dual_clock['strict_no_overlap_group_time_ns']:.6f}` ns",
        f"- strict no-overlap latency upper bound: `{dual_clock['strict_no_overlap_latency_upper_bound_us']:.6f}` us",
        f"- strict no-overlap throughput lower bound: `{dual_clock['strict_no_overlap_throughput_lower_bound_per_s']:.12f}` token/s",
        f"- conditional overlap group time: `{dual_clock['conditional_overlap_group_time_ns']:.6f}` ns",
        f"- conditional overlap latency lower bound: `{dual_clock['conditional_overlap_latency_lower_bound_us']:.6f}` us",
        f"- conditional overlap throughput upper bound: `{dual_clock['conditional_overlap_throughput_upper_bound_per_s']:.12f}` token/s",
        "",
        "## Remaining Abstractions",
        "",
    ]
    lines.extend(f"- {item}" for item in report["remaining_abstractions"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact-reduction-json", type=Path, required=True)
    parser.add_argument("--folded-global-json", type=Path, required=True)
    parser.add_argument("--pair-metrics", type=Path, required=True)
    parser.add_argument("--temporal-metrics", type=Path, required=True)
    parser.add_argument("--macro-top-metrics", type=Path, required=True)
    parser.add_argument("--macro-top-config", type=Path, required=True)
    parser.add_argument("--r6-diagnostic-json", type=Path, required=True)
    parser.add_argument("--reducer-probe-config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    report = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(_build_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

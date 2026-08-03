#!/usr/bin/env python3
"""Bound the measured folded global exact-reduction path for Llama7B."""

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

from npu.eval.probe_attention_score32_exact_partial_gqa8_dual_stream_producer import (  # noqa: E402
    build_report as build_dual_stream_producer_report,
)
from npu.sim.perf.attention_exact_partial import (  # noqa: E402
    FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    finalizer_accept_interval_cycles,
    finalizer_output_latency_cycles,
    exact_partial_tree_service_manifest,
)

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_folded_global_exact_reduction_recost_v2"
_DECISION = "folded_global_exact_reduction_bounded_recost_recorded"
_EXPECTED_SUPERSEDED_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_EXPECTED_SUPERSEDED_ITEM_ID = "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1"
_EXPECTED_CADENCE_DECISION = (
    "score32_986_cycle_arithmetic_not_sustained_by_corrected_group_command_mapping"
)
_EXPECTED_TREE_TOP = "attention_score32_exact_partial_tree_folded_mersenne_c16_r2"
_EXPECTED_ROOT_FINALIZER_TOP = "attention_score32_exact_root_finalizer_l8"
_EXPECTED_BANK_CONTROL_TOP = "attention_score32_exact_finalizer_bank_control_l8_b4"
_EXPECTED_DATASET_BASE = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1"
_EXPECTED_CLOCK_PERIOD_NS = 8.0
_EXPECTED_TREE_METRICS = {
    "critical_path_ns": 7.9837,
    "stdcell_area_um2": 789495.0,
    "total_power_mw": 4.15,
}
_EXPECTED_ROOT_FINALIZER_METRICS = {
    "critical_path_ns": 3.435,
    "stdcell_area_um2": 24311.1,
    "total_power_mw": 0.0128,
}
_EXPECTED_BANK_CONTROL_METRICS = {
    "critical_path_ns": 2.8512,
    "stdcell_area_um2": 5812.37,
    "total_power_mw": 0.00176,
}
_EXPECTED_OLD_TIMING = {
    "cross_tile_reduction_cycles": 574,
    "replica_recost_tile_service_cycles": 986,
    "tile_service_cycles": 986,
}
_EXPECTED_TREE_SERVICE = {
    "full_wave_root_outputs": 128,
    "full_wave_first_root_output_cycle": 80,
    "full_wave_last_root_output_cycle": 2620,
    "full_wave_drain_cycle": 2620,
    "pair_compute_launch_interval_cycles": 20,
}
_EXPECTED_PRODUCER_COMMAND_DRAINS = {
    "one_block": 337,
    "two_block": 528,
}
_EXPECTED_WORST_WAVE_DRAIN = 1536
_EXPECTED_GROUPS = 4
_EXPECTED_WAVES = 8
_EXPECTED_HEADS_PER_GROUP = 8
_EXPECTED_FINALIZER_BANKS = 4
_EXPECTED_FINALIZER_LANES = 8
_EXPECTED_FINALIZER_PER_BANK_OUTPUT_LATENCY = 58
_EXPECTED_FINALIZER_PER_BANK_ACCEPT_INTERVAL = 59


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


def _row_sha256(row: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _select_best_ok_metrics_row(path: Path, *, design: str) -> dict[str, Any]:
    rows = _load_metrics_rows(path)
    feasible_rows = [
        row
        for row in rows
        if row.get("status") == "ok"
        and row.get("design") == design
        and _as_float(row.get("critical_path_ns"), "metrics critical_path_ns")
        <= _EXPECTED_CLOCK_PERIOD_NS
    ]
    if not feasible_rows:
        raise ValueError(
            f"metrics file has no ok row meeting {_EXPECTED_CLOCK_PERIOD_NS} ns for {design}: {path}"
        )

    def _rank(row: dict[str, str]) -> tuple[float, float, float]:
        return (
            _as_float(row.get("stdcell_area_um2"), "metrics stdcell_area_um2"),
            _as_float(row.get("total_power_mw"), "metrics total_power_mw"),
            _as_float(row.get("critical_path_ns"), "metrics critical_path_ns"),
        )

    selected = min(feasible_rows, key=_rank)
    return {
        "design": design,
        "param_hash": str(selected.get("param_hash") or ""),
        "config_hash": str(selected.get("config_hash") or ""),
        "tag": str(selected.get("tag") or ""),
        "critical_path_ns": _as_float(selected.get("critical_path_ns"), "metrics critical_path_ns"),
        "stdcell_area_um2": _as_float(selected.get("stdcell_area_um2"), "metrics stdcell_area_um2"),
        "stdcell_count": _as_int(selected.get("stdcell_count"), "metrics stdcell_count"),
        "total_power_mw": _as_float(selected.get("total_power_mw"), "metrics total_power_mw"),
        "selection_policy": "min_area_then_power_then_critical_path_among_ok_rows_meeting_8ns",
        "row_sha256": _row_sha256(selected),
    }


def _validate_superseded_recost(payload: JsonDict) -> dict[str, Any]:
    _require_equal(payload.get("model"), _EXPECTED_SUPERSEDED_MODEL, "superseded recost model")
    best = payload.get("best_requested")
    if not isinstance(best, dict):
        raise ValueError("superseded recost missing best_requested")
    for key, expected in _EXPECTED_OLD_TIMING.items():
        _require_equal(best.get(key), expected, f"superseded recost {key}")
    return {
        "item_id": _EXPECTED_SUPERSEDED_ITEM_ID,
        "best_requested": {
            "cross_tile_reduction_cycles": int(best["cross_tile_reduction_cycles"]),
            "replica_recost_tile_service_cycles": int(best["replica_recost_tile_service_cycles"]),
            "tile_service_cycles": int(best["tile_service_cycles"]),
        },
    }


def _validate_cadence_audit(payload: JsonDict) -> dict[str, Any]:
    _require_equal(payload.get("decision"), _EXPECTED_CADENCE_DECISION, "cadence audit decision")
    revision = payload.get("functional_producer_revision")
    if not isinstance(revision, dict):
        raise ValueError("cadence audit missing functional_producer_revision")
    measured = revision.get("measured_service")
    mapping = revision.get("mapping")
    schedule = revision.get("group_major_reducer_schedule")
    interpretation = revision.get("interpretation")
    if not isinstance(measured, dict) or not isinstance(mapping, dict):
        raise ValueError("cadence audit missing measured producer mapping evidence")
    if not isinstance(schedule, dict) or not isinstance(interpretation, dict):
        raise ValueError("cadence audit missing group-major schedule evidence")
    _require_equal(measured.get("integrated_drain_cycles"), _EXPECTED_WORST_WAVE_DRAIN, "worst-wave drain cycles")
    _require_equal(measured.get("block_counts_per_stream"), [2, 1, 1, 1], "worst-wave block_counts_per_stream")
    _require_equal(schedule.get("gqa_groups"), _EXPECTED_GROUPS, "group-major gqa_groups")
    _require_equal(schedule.get("tile_waves"), _EXPECTED_WAVES, "group-major tile_waves")
    _require_equal(
        schedule.get("schedule_contract"),
        "process_one_fixed_gqa8_group_across_all_8_tile_waves_then_emit_finalize_before_next_head_base",
        "group-major schedule contract",
    )
    _require_equal(schedule.get("safe_interleave_status"), "not_established", "group-major safe interleave")
    _require_equal(
        interpretation.get("reference_986_cycles_sustained"),
        False,
        "cadence audit reference_986_cycles_sustained",
    )
    p53 = mapping.get("distribution_for_53_datapaths")
    p54 = mapping.get("distribution_for_54_datapaths")
    if not isinstance(p53, dict) or not isinstance(p54, dict):
        raise ValueError("cadence audit missing p53/p54 mapping")
    _require_equal(p53.get("datapaths_with_one_two_block_command"), 44, "p53 two-block coverage")
    _require_equal(p54.get("datapaths_with_one_two_block_command"), 40, "p54 two-block coverage")
    _require_equal(p53.get("datapaths_with_zero_two_block_commands"), 9, "p53 zero-two-block coverage")
    _require_equal(p54.get("datapaths_with_zero_two_block_commands"), 14, "p54 zero-two-block coverage")
    return {
        "decision": str(payload["decision"]),
        "worst_loaded_single_datapath_wave_cycles": int(measured["integrated_drain_cycles"]),
        "worst_loaded_block_counts_per_stream": [int(value) for value in measured["block_counts_per_stream"]],
        "group_major_schedule_contract": str(schedule["schedule_contract"]),
        "safe_interleave_status": str(schedule["safe_interleave_status"]),
        "p53_distribution": {
            "dual_stream_datapaths": int(p53["dual_stream_datapaths"]),
            "datapaths_with_one_two_block_command": int(p53["datapaths_with_one_two_block_command"]),
            "datapaths_with_zero_two_block_commands": int(p53["datapaths_with_zero_two_block_commands"]),
        },
        "p54_distribution": {
            "dual_stream_datapaths": int(p54["dual_stream_datapaths"]),
            "datapaths_with_one_two_block_command": int(p54["datapaths_with_one_two_block_command"]),
            "datapaths_with_zero_two_block_commands": int(p54["datapaths_with_zero_two_block_commands"]),
        },
        "reference_986_cycles_sustained": False,
    }


def _validate_tree_config(payload: JsonDict) -> None:
    body = payload.get("attention_score32_exact_partial_tree")
    if not isinstance(body, dict):
        raise ValueError("tree config missing attention_score32_exact_partial_tree")
    _require_equal(payload.get("top_name"), _EXPECTED_TREE_TOP, "tree top_name")
    _require_equal(body.get("clusters"), 16, "tree clusters")
    _require_equal(body.get("radix"), 2, "tree radix")
    _require_equal(body.get("value_slices"), 16, "tree value_slices")
    _require_equal(body.get("head_id_bits"), 5, "tree head_id_bits")
    _require_equal(
        body.get("pair_node_impl"),
        FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
        "tree pair_node_impl",
    )
    _require_equal(body.get("exp_scale_impl"), "factored_h33_l64_mul_exact", "tree exp_scale_impl")


def _validate_root_finalizer_config(payload: JsonDict) -> None:
    body = payload.get("attention_score32_exact_root_finalizer")
    if not isinstance(body, dict):
        raise ValueError("root finalizer config missing attention_score32_exact_root_finalizer")
    _require_equal(payload.get("top_name"), _EXPECTED_ROOT_FINALIZER_TOP, "root finalizer top_name")
    _require_equal(body.get("divider_lanes"), _EXPECTED_FINALIZER_LANES, "root finalizer divider_lanes")
    _require_equal(body.get("value_slices"), 16, "root finalizer value_slices")
    _require_equal(body.get("head_id_bits"), 5, "root finalizer head_id_bits")


def _validate_bank_control_config(payload: JsonDict) -> None:
    body = payload.get("attention_score32_exact_finalizer_bank_control")
    if not isinstance(body, dict):
        raise ValueError("bank-control config missing attention_score32_exact_finalizer_bank_control")
    _require_equal(payload.get("top_name"), _EXPECTED_BANK_CONTROL_TOP, "bank-control top_name")
    _require_equal(body.get("finalizer_banks"), _EXPECTED_FINALIZER_BANKS, "bank-control finalizer_banks")
    _require_equal(body.get("divider_lanes"), _EXPECTED_FINALIZER_LANES, "bank-control divider_lanes")
    _require_equal(body.get("value_slices"), 16, "bank-control value_slices")
    _require_equal(body.get("head_id_bits"), 5, "bank-control head_id_bits")


def _validate_metrics(row: dict[str, Any], expected: dict[str, float], label: str) -> None:
    for key, value in expected.items():
        _require_equal(row[key], value, f"{label} {key}")


def _producer_command_drain_cycles(config: JsonDict, *, blocks_per_stream: int) -> int:
    report = build_dual_stream_producer_report(
        config=config,
        heads=32,
        command_count=1,
        blocks_per_stream=blocks_per_stream,
        head_dim=128,
        head_bases=(0,),
        stress_interfaces=False,
    )
    return int(report["integrated_drain_cycles"])


def _file_record(path: Path, payload: JsonDict | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": _portable_path(path),
        "file_sha256": _sha256_file(path),
    }
    if payload is not None:
        record["canonical_json_sha256"] = _canonical_json_sha256(payload)
    return record


def build_report(args: argparse.Namespace) -> JsonDict:
    superseded_recost_path = Path(args.superseded_recost_json).resolve()
    cadence_audit_path = Path(args.cadence_audit_json).resolve()
    tree_config_path = Path(args.tree_config).resolve()
    tree_metrics_path = Path(args.tree_metrics).resolve()
    root_finalizer_config_path = Path(args.root_finalizer_config).resolve()
    root_finalizer_metrics_path = Path(args.root_finalizer_metrics).resolve()
    bank_control_config_path = Path(args.bank_control_config).resolve()
    bank_control_metrics_path = Path(args.bank_control_metrics).resolve()
    producer_config_path = Path(args.producer_config).resolve()
    producer_probe_path = Path(args.producer_probe_script).resolve()
    exact_partial_path = Path(args.exact_partial_module).resolve()

    superseded_payload = _load_json(superseded_recost_path)
    cadence_payload = _load_json(cadence_audit_path)
    tree_config = _load_json(tree_config_path)
    root_finalizer_config = _load_json(root_finalizer_config_path)
    bank_control_config = _load_json(bank_control_config_path)
    producer_config = _load_json(producer_config_path)

    superseded = _validate_superseded_recost(superseded_payload)
    cadence = _validate_cadence_audit(cadence_payload)
    _validate_tree_config(tree_config)
    _validate_root_finalizer_config(root_finalizer_config)
    _validate_bank_control_config(bank_control_config)

    tree_row = _select_best_ok_metrics_row(tree_metrics_path, design=_EXPECTED_TREE_TOP)
    root_row = _select_best_ok_metrics_row(root_finalizer_metrics_path, design=_EXPECTED_ROOT_FINALIZER_TOP)
    bank_control_row = _select_best_ok_metrics_row(bank_control_metrics_path, design=_EXPECTED_BANK_CONTROL_TOP)
    _validate_metrics(tree_row, _EXPECTED_TREE_METRICS, "tree metrics")
    _validate_metrics(root_row, _EXPECTED_ROOT_FINALIZER_METRICS, "root finalizer metrics")
    _validate_metrics(bank_control_row, _EXPECTED_BANK_CONTROL_METRICS, "bank-control metrics")

    tree_service = exact_partial_tree_service_manifest(
        clusters=16,
        heads=_EXPECTED_HEADS_PER_GROUP,
        pair_node_impl=FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
    )
    for key, expected in _EXPECTED_TREE_SERVICE.items():
        _require_equal(tree_service.get(key), expected, f"tree service {key}")

    per_bank_output_latency = finalizer_output_latency_cycles(_EXPECTED_FINALIZER_LANES)
    per_bank_accept_interval = finalizer_accept_interval_cycles(_EXPECTED_FINALIZER_LANES)
    _require_equal(
        per_bank_output_latency,
        _EXPECTED_FINALIZER_PER_BANK_OUTPUT_LATENCY,
        "finalizer per-bank output latency",
    )
    _require_equal(
        per_bank_accept_interval,
        _EXPECTED_FINALIZER_PER_BANK_ACCEPT_INTERVAL,
        "finalizer per-bank accept interval",
    )

    tree_ii = int(tree_service["pair_compute_launch_interval_cycles"])
    minimum_banks = math.ceil(per_bank_accept_interval / tree_ii)
    _require_equal(minimum_banks, 3, "minimum banks for tree/finalizer overlap")
    same_bank_revisit_cycles = tree_ii * _EXPECTED_FINALIZER_BANKS
    if same_bank_revisit_cycles < per_bank_accept_interval:
        raise ValueError("b4 control does not provide enough same-bank revisit spacing")
    composed_global_final_output_drain_cycles = (
        int(tree_service["full_wave_last_root_output_cycle"]) + per_bank_output_latency
    )
    _require_equal(composed_global_final_output_drain_cycles, 2678, "composed global final output drain cycles")

    one_block_drain = _producer_command_drain_cycles(producer_config, blocks_per_stream=1)
    two_block_drain = _producer_command_drain_cycles(producer_config, blocks_per_stream=2)
    _require_equal(one_block_drain, _EXPECTED_PRODUCER_COMMAND_DRAINS["one_block"], "one-block producer drain")
    _require_equal(two_block_drain, _EXPECTED_PRODUCER_COMMAND_DRAINS["two_block"], "two-block producer drain")

    conservative_cluster_barrier_per_wave_group = two_block_drain
    conservative_cluster_barrier_per_group = conservative_cluster_barrier_per_wave_group * _EXPECTED_WAVES
    strict_serialized_group_bound = (
        conservative_cluster_barrier_per_group + composed_global_final_output_drain_cycles
    )
    strict_serialized_all_groups_bound = strict_serialized_group_bound * _EXPECTED_GROUPS
    overlap_margin_cycles = conservative_cluster_barrier_per_group - composed_global_final_output_drain_cycles
    _require_equal(conservative_cluster_barrier_per_group, 4224, "conservative cluster barrier per group")
    _require_equal(strict_serialized_group_bound, 6902, "strict serialized group bound")
    _require_equal(strict_serialized_all_groups_bound, 27608, "strict serialized all-groups bound")
    _require_equal(overlap_margin_cycles, 1546, "conditional overlap margin")

    composed_area_um2 = round(
        tree_row["stdcell_area_um2"]
        + (_EXPECTED_GROUPS * root_row["stdcell_area_um2"])
        + bank_control_row["stdcell_area_um2"],
        2,
    )
    composed_power_mw = round(
        tree_row["total_power_mw"]
        + (_EXPECTED_GROUPS * root_row["total_power_mw"])
        + bank_control_row["total_power_mw"],
        5,
    )
    composed_stdcell_count = (
        tree_row["stdcell_count"]
        + (_EXPECTED_GROUPS * root_row["stdcell_count"])
        + bank_control_row["stdcell_count"]
    )
    composed_critical_path_ns = max(
        tree_row["critical_path_ns"],
        root_row["critical_path_ns"],
        bank_control_row["critical_path_ns"],
    )

    return {
        "version": 2,
        "model": _MODEL,
        "decision": _DECISION,
        "quality_rerun_required": False,
        "quality_rerun_reason": "Exact precision semantics are unchanged; this is a timing/ppa recost only.",
        "supersession": {
            "supersedes_only_old_timing_assumptions": True,
            "superseded_source_item_id": superseded["item_id"],
            "superseded_timing_contract": superseded["best_requested"],
            "source_evidence_preserved": True,
            "superseded_assumption_summary": (
                "Do not reuse the older 574-cycle global reduction drain as if it sat directly on a sustained "
                "986-cycle producer. The 986-cycle arithmetic reference was already broken by the corrected "
                "producer cadence audit, and the local 53/54-way group-major reducer remains unresolved."
            ),
        },
        "source_artifacts": {
            "superseded_recost_json": _file_record(superseded_recost_path, superseded_payload),
            "cadence_audit_json": _file_record(cadence_audit_path, cadence_payload),
            "tree_config_json": _file_record(tree_config_path, tree_config),
            "tree_metrics_csv": _file_record(tree_metrics_path),
            "root_finalizer_config_json": _file_record(root_finalizer_config_path, root_finalizer_config),
            "root_finalizer_metrics_csv": _file_record(root_finalizer_metrics_path),
            "bank_control_config_json": _file_record(bank_control_config_path, bank_control_config),
            "bank_control_metrics_csv": _file_record(bank_control_metrics_path),
            "producer_config_json": _file_record(producer_config_path, producer_config),
            "producer_probe_script": _file_record(producer_probe_path),
            "exact_partial_module": _file_record(exact_partial_path),
        },
        "cadence_evidence": cadence,
        "producer_command_service_evidence": {
            "source_config": _portable_path(producer_config_path),
            "source_probe_script": _portable_path(producer_probe_path),
            "ideal_interface_mode": True,
            "head_dim": 128,
            "heads": 32,
            "one_block_command_drain_cycles": one_block_drain,
            "two_block_command_drain_cycles": two_block_drain,
            "cluster_barrier_reason": (
                "p53/p54 mapping guarantees at least one 2-block producer command per cluster for every "
                "GQA8 head group in each wave"
            ),
            "conservative_cluster_barrier_per_wave_group_cycles": conservative_cluster_barrier_per_wave_group,
            "conservative_cluster_barrier_per_group_cycles": conservative_cluster_barrier_per_group,
            "distinguished_from_single_datapath_worst_wave_cycles": _EXPECTED_WORST_WAVE_DRAIN,
        },
        "global_folded_tree_service": {
            "source_function": "npu.sim.perf.attention_exact_partial.exact_partial_tree_service_manifest",
            "clusters": 16,
            "heads": _EXPECTED_HEADS_PER_GROUP,
            "pair_node_impl": FOLDED_SHARED_SCALE_MERSENNE_EXACT_PARTIAL_TREE_PAIR_NODE_IMPL,
            "root_beats": int(tree_service["full_wave_root_outputs"]),
            "first_root_output_cycle": int(tree_service["full_wave_first_root_output_cycle"]),
            "last_root_output_cycle": int(tree_service["full_wave_last_root_output_cycle"]),
            "drain_cycle": int(tree_service["full_wave_drain_cycle"]),
            "root_output_initiation_interval_cycles": tree_ii,
        },
        "finalizer_contract": {
            "source_function": "npu.sim.perf.attention_exact_partial.finalizer_output_latency_cycles",
            "divider_lanes": _EXPECTED_FINALIZER_LANES,
            "measured_bank_control_banks": _EXPECTED_FINALIZER_BANKS,
            "minimum_banks_for_tree_ii": minimum_banks,
            "per_bank_output_latency_cycles": per_bank_output_latency,
            "per_bank_accept_interval_cycles": per_bank_accept_interval,
            "same_bank_revisit_cycles_with_b4": same_bank_revisit_cycles,
            "composed_global_final_output_drain_cycles": composed_global_final_output_drain_cycles,
            "composed_global_drain_convention": (
                "final output cycle after the tree root stream hands its last beat to the measured b4-controlled "
                "L8 finalizer bank set"
            ),
        },
        "measured_component_ppa_estimate": {
            "clocking_claim": (
                "No composed-route claim. The estimate sums measured standalone Nangate45 vectorless component rows "
                "and uses max(component critical_path_ns) as a bounded timing anchor only."
            ),
            "vectorless_power_caveat": True,
            "tree_row": tree_row,
            "root_finalizer_row": root_row,
            "bank_control_row": bank_control_row,
            "composed_global_exact_reduction_path": {
                "components": {
                    "folded_tree_instances": 1,
                    "root_finalizer_instances": _EXPECTED_GROUPS,
                    "bank_control_instances": 1,
                },
                "estimated_critical_path_ns": composed_critical_path_ns,
                "estimated_stdcell_area_um2": composed_area_um2,
                "estimated_stdcell_count": composed_stdcell_count,
                "estimated_total_power_mw": composed_power_mw,
            },
        },
        "bounded_schedule_analysis": {
            "strict_serialized_bound_per_group_cycles": strict_serialized_group_bound,
            "strict_serialized_bound_all_4_groups_cycles": strict_serialized_all_groups_bound,
            "strict_serialized_formula": "4224(cluster barrier) + 2678(global folded tree plus measured b4/L8 finalizer) = 6902 per group",
            "conditional_overlap_margin_cycles": overlap_margin_cycles,
            "conditional_overlap_lower_bound_status": "not_established",
            "conditional_overlap_requirement": (
                "Requires double-buffered local aggregate availability and a proven safe next-group overlap scheduler."
            ),
            "conditional_overlap_note": (
                "The 1546-cycle slack only shows that the measured global folded tree/finalizer path can fit under "
                "the conservative 4224-cycle cluster barrier if next-group overlap is made safe. That scheduler and "
                "the local 53/54-way persistent reducer are still unresolved."
            ),
            "single_datapath_worst_wave_cycles": _EXPECTED_WORST_WAVE_DRAIN,
            "single_datapath_worst_wave_scope": (
                "ideal-interface functional simulation for one worst-loaded datapath wave only; not a per-cluster or "
                "group-complete service bound"
            ),
        },
        "decision_summary": {
            "global_folded_tree_finalizer_physically_plausible": True,
            "necessarily_throughput_dominant": False,
            "immediate_unresolved_frontier": (
                "local p53/p54 53/54-way exact reducer with 8-wave persistent group-major state plus a safe overlap scheduler"
            ),
            "do_not_start_global_tree_before_local_group_aggregate": True,
        },
        "remaining_abstractions": [
            "The local 53/54-way exact reducer that emits one valid group aggregate per cluster is still unmeasured.",
            "Safe overlap between successive groups is not established; the 1546-cycle margin is conditional only.",
            "The composed PPA estimate is a vectorless sum of standalone component rows and not a routed composed macro.",
            "No 328-bit transport, NoC, SRAM, or local-reducer activity-power closure is claimed here.",
        ],
        "summary": {
            "old_global_reduction_drain_cycles": 574,
            "old_arithmetic_reference_cycles": 986,
            "corrected_single_datapath_worst_wave_cycles": _EXPECTED_WORST_WAVE_DRAIN,
            "conservative_cluster_barrier_per_group_cycles": conservative_cluster_barrier_per_group,
            "global_final_output_drain_cycles": composed_global_final_output_drain_cycles,
            "strict_serialized_bound_per_group_cycles": strict_serialized_group_bound,
            "strict_serialized_bound_all_4_groups_cycles": strict_serialized_all_groups_bound,
            "estimated_component_critical_path_ns": composed_critical_path_ns,
            "estimated_component_area_um2": composed_area_um2,
            "estimated_component_power_mw": composed_power_mw,
        },
    }


def _build_markdown(report: JsonDict) -> str:
    ppa = report["measured_component_ppa_estimate"]["composed_global_exact_reduction_path"]
    bounds = report["bounded_schedule_analysis"]
    cadence = report["cadence_evidence"]
    finalizer = report["finalizer_contract"]
    tree = report["global_folded_tree_service"]
    producer = report["producer_command_service_evidence"]
    lines = [
        "# Folded Global Exact Reduction Recost",
        "",
        f"- decision: `{report['decision']}`",
        f"- superseded timing source: `{report['source_artifacts']['superseded_recost_json']['path']}`",
        f"- cadence audit: `{report['source_artifacts']['cadence_audit_json']['path']}`",
        f"- quality rerun required: `{str(report['quality_rerun_required']).lower()}`",
        "",
        "## Measured Component Estimate",
        "",
        "| component | critical path ns | area um2 | power mW |",
        "| --- | ---: | ---: | ---: |",
        (
            f"| folded c16 tree | {report['measured_component_ppa_estimate']['tree_row']['critical_path_ns']:.4f} | "
            f"{report['measured_component_ppa_estimate']['tree_row']['stdcell_area_um2']:.1f} | "
            f"{report['measured_component_ppa_estimate']['tree_row']['total_power_mw']:.5f} |"
        ),
        (
            f"| root finalizer L8 x4 | {report['measured_component_ppa_estimate']['root_finalizer_row']['critical_path_ns']:.4f} | "
            f"{4 * report['measured_component_ppa_estimate']['root_finalizer_row']['stdcell_area_um2']:.1f} | "
            f"{4 * report['measured_component_ppa_estimate']['root_finalizer_row']['total_power_mw']:.5f} |"
        ),
        (
            f"| bank control b4 | {report['measured_component_ppa_estimate']['bank_control_row']['critical_path_ns']:.4f} | "
            f"{report['measured_component_ppa_estimate']['bank_control_row']['stdcell_area_um2']:.2f} | "
            f"{report['measured_component_ppa_estimate']['bank_control_row']['total_power_mw']:.5f} |"
        ),
        (
            f"| composed estimate | {ppa['estimated_critical_path_ns']:.4f} | "
            f"{ppa['estimated_stdcell_area_um2']:.2f} | {ppa['estimated_total_power_mw']:.5f} |"
        ),
        "",
        "Vectorless power only. No composed-route claim is made.",
        "",
        "## Schedule Bounds",
        "",
        (
            f"- corrected worst-loaded single-datapath wave: `{cadence['worst_loaded_single_datapath_wave_cycles']}` cycles "
            f"for block counts `{cadence['worst_loaded_block_counts_per_stream']}`"
        ),
        (
            f"- conservative per-cluster barrier: `{producer['two_block_command_drain_cycles']}` cycles per wave/group, "
            f"`{producer['conservative_cluster_barrier_per_group_cycles']}` cycles across 8 waves"
        ),
        (
            f"- folded c16 global tree service: `{tree['root_beats']}` beats, first `{tree['first_root_output_cycle']}`, "
            f"last/drain `{tree['drain_cycle']}`, II `{tree['root_output_initiation_interval_cycles']}`"
        ),
        (
            f"- measured finalizer contract: per-bank output latency `{finalizer['per_bank_output_latency_cycles']}`, "
            f"accept interval `{finalizer['per_bank_accept_interval_cycles']}`, minimum banks `{finalizer['minimum_banks_for_tree_ii']}`, "
            f"measured point `b4`, same-bank revisit `{finalizer['same_bank_revisit_cycles_with_b4']}`"
        ),
        (
            f"- composed global final output drain: `{finalizer['composed_global_final_output_drain_cycles']}` cycles"
        ),
        (
            f"- strict serialized bound: `{bounds['strict_serialized_bound_per_group_cycles']}` cycles per group, "
            f"`{bounds['strict_serialized_bound_all_4_groups_cycles']}` cycles for 4 groups"
        ),
        (
            f"- conditional overlap margin: `{bounds['conditional_overlap_margin_cycles']}` cycles, status "
            f"`{bounds['conditional_overlap_lower_bound_status']}`"
        ),
        "",
        "Do not start the global folded tree before the local 53/54-way group-major reducer emits valid per-cluster group aggregates.",
        "",
        "## Decision",
        "",
        "- The measured folded global tree plus measured L8/b4 finalizer path is physically plausible.",
        "- It is not necessarily throughput-dominant under the current evidence.",
        "- The immediate unresolved frontier is the local p53/p54 persistent reducer and the overlap scheduler.",
        "",
        "## Remaining Abstractions",
        "",
    ]
    lines.extend(f"- {item}" for item in report["remaining_abstractions"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--superseded-recost-json", type=Path, required=True)
    parser.add_argument("--cadence-audit-json", type=Path, required=True)
    parser.add_argument("--tree-config", type=Path, required=True)
    parser.add_argument("--tree-metrics", type=Path, required=True)
    parser.add_argument("--root-finalizer-config", type=Path, required=True)
    parser.add_argument("--root-finalizer-metrics", type=Path, required=True)
    parser.add_argument("--bank-control-config", type=Path, required=True)
    parser.add_argument("--bank-control-metrics", type=Path, required=True)
    parser.add_argument("--producer-config", type=Path, required=True)
    parser.add_argument("--producer-probe-script", type=Path, required=True)
    parser.add_argument("--exact-partial-module", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)

    report = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(_build_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

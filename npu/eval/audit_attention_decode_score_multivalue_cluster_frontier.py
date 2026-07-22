#!/usr/bin/env python3
"""Recost the Llama7B decode frontier with the shared-score multivalue cluster."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]

_EXPECTED_ACTIVITY_MODEL = "decoder_attention_decode_score_multivalue_cluster_activity_power_v1"
_EXPECTED_ACTIVITY_DECISION = "activity_backed_cluster_power_measured"
_EXPECTED_EQUIVALENCE_DECISION = "decode_score_multivalue_cluster_equivalence_pass"
_EXPECTED_PRECISION_STATUS = "unchanged_integer_contract_from_merged_multivalue_equivalence"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _source_schedule(frontier: JsonDict, frontier_path: Path) -> tuple[JsonDict, str]:
    schedule = frontier.get("source_schedule")
    if isinstance(schedule, dict):
        return schedule, str(frontier_path)
    inputs = frontier.get("inputs")
    linked = inputs.get("prior_frontier_json") if isinstance(inputs, dict) else None
    if not isinstance(linked, str) or not linked:
        raise ValueError("prior frontier lacks source_schedule and a prior_frontier_json linkage")
    linked_path = Path(linked)
    if not linked_path.is_absolute():
        linked_path = Path.cwd() / linked_path
    source = _load(linked_path)
    schedule = source.get("source_schedule")
    if not isinstance(schedule, dict):
        raise ValueError(f"linked prior frontier lacks source_schedule: {linked}")
    return schedule, linked


def _positive(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def _nonnegative(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} must be finite and nonnegative")
    return result


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a positive integer") from exc
    if not math.isfinite(numeric) or numeric <= 0 or not numeric.is_integer():
        raise ValueError(f"{label} must be a positive integer")
    return int(numeric)


def _nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a nonnegative integer")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a nonnegative integer") from exc
    if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
        raise ValueError(f"{label} must be a nonnegative integer")
    return int(numeric)


def _validated_activity_best(activity_report: JsonDict) -> JsonDict:
    if activity_report.get("model") != _EXPECTED_ACTIVITY_MODEL:
        raise ValueError("activity-power report has an unexpected model")
    if activity_report.get("decision") != _EXPECTED_ACTIVITY_DECISION:
        raise ValueError("activity-power report has an unexpected decision")
    if activity_report.get("promotion_gate_pass") is not True:
        raise ValueError("activity-power promotion gate did not pass")
    best = activity_report.get("best")
    if not isinstance(best, dict) or not isinstance(best.get("ppa_metric"), dict) or not isinstance(
        best.get("activity_power"), dict
    ):
        raise ValueError("activity-power report lacks a promoted best candidate")
    candidate_id = best.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("activity-power best candidate lacks an identity")
    if activity_report.get("best_candidate_id") != candidate_id:
        raise ValueError("activity-power best candidate identity does not match")
    if best.get("status") != "activity_backed":
        raise ValueError("activity-power best candidate is not activity-backed")
    if best["activity_power"].get("promotion_gate_pass") is not True:
        raise ValueError("activity-power best candidate promotion gate did not pass")
    if activity_report.get("precision_status") != _EXPECTED_PRECISION_STATUS:
        raise ValueError("activity-power report has an unexpected precision status")
    equivalence = activity_report.get("equivalence")
    if not isinstance(equivalence, dict) or equivalence.get("equivalence_pass") is not True:
        raise ValueError("activity-power equivalence did not pass")
    if equivalence.get("decision") != _EXPECTED_EQUIVALENCE_DECISION:
        raise ValueError("activity-power equivalence has an unexpected decision")
    for field in ("score_tensor_hash", "final_tensor_hash"):
        value = equivalence.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"activity-power equivalence lacks {field}")
    return best


def _activity_energy(activity: JsonDict) -> JsonDict:
    phases = activity.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ValueError("activity report lacks phase power")
    dynamic_j = 0.0
    leakage_j = 0.0
    phase_cycles = 0
    for phase in phases:
        if not isinstance(phase, dict):
            raise ValueError("activity phase is not an object")
        cycles = _positive_int(phase["full_context_cycles"], "phase full-context cycles")
        clock_ns = _positive(phase["clock_period_ns"], "phase clock")
        power = phase.get("power")
        if not isinstance(power, dict):
            raise ValueError("activity phase lacks power")
        dynamic_j += (_nonnegative(power["internal_w"], "internal power") + _nonnegative(
            power["switching_w"], "switching power"
        )) * cycles * clock_ns * 1.0e-9
        leakage_j += _nonnegative(power["leakage_w"], "leakage power") * cycles * clock_ns * 1.0e-9
        phase_cycles += cycles
    total_j = dynamic_j + leakage_j
    recorded = _positive(activity["full_context_energy_j"], "full-context energy")
    if not math.isclose(total_j, recorded, rel_tol=1.0e-6, abs_tol=1.0e-15):
        raise ValueError("phase energy does not match recorded full-context energy")
    if phase_cycles != _positive_int(activity["full_context_cycles"], "full-context cycles"):
        raise ValueError("phase cycles do not match full-context cycles")
    return {
        "dynamic_j_per_head_command": dynamic_j,
        "service_window_leakage_j_per_head_command": leakage_j,
        "modeled_service_j_per_head_command": total_j,
    }


def _row(
    *,
    cluster_count: int,
    schedule: JsonDict,
    cluster_metric: JsonDict,
    command_cycles: int,
    activity_clock_ns: float,
    energy: JsonDict,
    dense_tile: JsonDict,
) -> JsonDict:
    heads = _positive_int(schedule["attention_heads"], "attention heads")
    layers = _positive_int(schedule["layers"], "layers")
    hidden = _positive_int(schedule["hidden_size"], "hidden size")
    kv_heads = _positive_int(schedule["kv_heads"], "KV heads")
    head_dim = hidden // heads
    if cluster_count < 1 or cluster_count > heads:
        raise ValueError(f"cluster count must be in [1, {heads}]")
    cluster_area_um2 = _positive(cluster_metric["instance_area_um2"], "cluster area")
    dense_area_um2 = _positive(dense_tile["area_um2"], "dense QKV tile area")
    dense_macs = _positive(dense_tile["effective_macs_per_cycle"], "dense QKV MAC/cycle")
    budget_um2 = _positive(schedule["compute_budget_um2"], "logic compute budget")
    logic_area_used_um2 = _nonnegative(schedule["logic_area_used_um2"], "logic area used")
    compute_area_um2 = _nonnegative(schedule["compute_area_um2"], "compute area")
    noncompute_logic_um2 = logic_area_used_um2 - compute_area_um2
    if noncompute_logic_um2 < 0:
        raise ValueError("retained noncompute logic area must be nonnegative")
    available_compute_um2 = budget_um2 - noncompute_logic_um2
    cluster_total_um2 = cluster_count * cluster_area_um2
    qkv_useful_limit = hidden // 8 + 2 * kv_heads * head_dim // 8
    dense_count = min(
        qkv_useful_limit,
        max(0, math.floor((available_compute_um2 - cluster_total_um2) / dense_area_um2)),
    )
    area_fit = (
        dense_count > 0
        and noncompute_logic_um2 + cluster_total_um2 + dense_count * dense_area_um2 <= budget_um2
    )
    qkv_work = hidden**2 + 2 * hidden * kv_heads * head_dim
    qkv_cycles = math.ceil(qkv_work / (dense_count * dense_macs)) if dense_count else None
    waves = math.ceil(heads / cluster_count)
    attention_cycles = waves * command_cycles
    fixed_cycles = _nonnegative_int(
        schedule.get("command_dispatch_cycles", 0), "command dispatch cycles"
    ) + _nonnegative_int(
        schedule.get("kv_write_cycles", 0), "KV write cycles"
    )
    layer_cycles = qkv_cycles + attention_cycles + fixed_cycles if qkv_cycles is not None else None
    schedule_clock_ns = _positive(schedule["clock_ns"], "schedule clock")
    if schedule_clock_ns > activity_clock_ns:
        raise ValueError("schedule clock is slower than the measured activity clock")
    clock_ns = activity_clock_ns
    total_cycles = layer_cycles * layers if layer_cycles is not None else None
    latency_us = total_cycles * clock_ns / 1000.0 if total_cycles is not None else None
    logic_area_um2 = noncompute_logic_um2 + cluster_total_um2 + dense_count * dense_area_um2
    sram_area_um2 = float(schedule.get("measured_shared_sram_used_area_um2", 0.0)) + float(
        schedule.get("measured_tile_local_sram_area_um2", 0.0)
    )
    active_commands_per_token = heads * layers
    deployed_command_slots = cluster_count * waves * layers
    dynamic_j = active_commands_per_token * float(energy["dynamic_j_per_head_command"])
    leakage_j = deployed_command_slots * float(
        energy["service_window_leakage_j_per_head_command"]
    )
    component_energy_j = dynamic_j + leakage_j
    return {
        "candidate_id": f"decode_score_multivalue_cluster_c{cluster_count}",
        "cluster_count": cluster_count,
        "head_commands_per_layer": heads,
        "cluster_waves_per_layer": waves,
        "dense_qkv_tile_count": dense_count,
        "dense_qkv_useful_parallelism_limit": qkv_useful_limit,
        "qkv_cycles": qkv_cycles,
        "attention_cycles": attention_cycles,
        "fixed_cycles": fixed_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "clock_ns": clock_ns,
        "latency_us": round(latency_us, 6) if latency_us is not None else None,
        "token_throughput_per_s": round(1.0e6 / latency_us, 12) if latency_us else None,
        "cluster_area_mm2": round(cluster_total_um2 / 1.0e6, 9),
        "dense_qkv_area_mm2": round(dense_count * dense_area_um2 / 1.0e6, 9),
        "retained_noncompute_logic_area_mm2": round(noncompute_logic_um2 / 1.0e6, 9),
        "compute_budget_slack_mm2": round(
            (
                budget_um2
                - noncompute_logic_um2
                - cluster_total_um2
                - dense_count * dense_area_um2
            )
            / 1.0e6,
            9,
        ),
        "logic_area_mm2": round(logic_area_um2 / 1.0e6, 9),
        "embodied_logic_plus_shared_sram_area_mm2": round(
            (logic_area_um2 + sram_area_um2) / 1.0e6, 9
        ),
        "compute_budget_area_fit": area_fit,
        "timing_feasible": (
            _positive(cluster_metric["critical_path_ns"], "cluster path") <= clock_ns
        ),
        "attention_cluster_dynamic_energy_mj_per_token": dynamic_j * 1.0e3,
        "attention_cluster_service_window_leakage_energy_mj_per_token": leakage_j * 1.0e3,
        "attention_cluster_modeled_service_energy_mj_per_token": component_energy_j * 1.0e3,
        "energy_status": (
            "activity_backed_attention_cluster_service_windows_only_"
            "total_token_energy_incomplete"
        ),
    }


def _pareto(rows: list[JsonDict]) -> list[JsonDict]:
    feasible = [row for row in rows if row["compute_budget_area_fit"] and row["timing_feasible"]]
    result = []
    for row in feasible:
        dominated = any(
            other is not row
            and float(other["latency_us"]) <= float(row["latency_us"])
            and float(other["embodied_logic_plus_shared_sram_area_mm2"])
            <= float(row["embodied_logic_plus_shared_sram_area_mm2"])
            and float(other["attention_cluster_modeled_service_energy_mj_per_token"])
            <= float(row["attention_cluster_modeled_service_energy_mj_per_token"])
            and (
                float(other["latency_us"]) < float(row["latency_us"])
                or float(other["embodied_logic_plus_shared_sram_area_mm2"])
                < float(row["embodied_logic_plus_shared_sram_area_mm2"])
                or float(other["attention_cluster_modeled_service_energy_mj_per_token"])
                < float(row["attention_cluster_modeled_service_energy_mj_per_token"])
            )
            for other in feasible
        )
        if not dominated:
            result.append(row)
    return result


def build_report(
    *, prior_frontier_json: Path, activity_power_json: Path, cluster_counts: list[int]
) -> JsonDict:
    prior = _load(prior_frontier_json)
    activity_report = _load(activity_power_json)
    best = _validated_activity_best(activity_report)
    schedule, schedule_source = _source_schedule(prior, prior_frontier_json)
    hidden = _positive_int(schedule["hidden_size"], "hidden size")
    heads = _positive_int(schedule["attention_heads"], "attention heads")
    _positive_int(schedule["sequence_length"], "sequence length")
    _positive_int(schedule["layers"], "layers")
    _positive_int(schedule["kv_heads"], "KV heads")
    if hidden != 4096 or heads != 32:
        raise ValueError("frontier is not the expected Llama7B 4096D/32-head schedule")
    validated_cluster_counts = [
        _positive_int(count, "cluster count") for count in cluster_counts
    ]
    for count in validated_cluster_counts:
        if count > heads:
            raise ValueError(f"cluster count must be in [1, {heads}]")
        if heads % count != 0:
            raise ValueError(f"cluster count {count} does not divide {heads} heads")
    dense_tile = prior.get("dense_qkv_tile")
    if not isinstance(dense_tile, dict):
        raise ValueError("prior frontier lacks measured dense_qkv_tile evidence")
    activity = best["activity_power"]
    command_cycles = _positive_int(activity["full_context_cycles"], "full-context cycles")
    activity_clock_ns = _positive(
        activity.get(
            "clock_period_ns",
            activity_report.get("activity_contract", {}).get("clock_period_ns"),
        ),
        "activity clock",
    )
    energy = _activity_energy(activity)
    phase_cycles = {
        str(phase.get("phase", phase.get("name", f"phase_{index}"))): int(
            phase["full_context_cycles"]
        )
        for index, phase in enumerate(activity["phases"])
    }
    rows = [
        _row(
            cluster_count=count,
            schedule=schedule,
            cluster_metric=best["ppa_metric"],
            command_cycles=command_cycles,
            activity_clock_ns=activity_clock_ns,
            energy=energy,
            dense_tile=dense_tile,
        )
        for count in validated_cluster_counts
    ]
    pareto_rows = _pareto(rows)
    if not pareto_rows:
        raise ValueError("no feasible multivalue-cluster frontier row")
    best_throughput = max(pareto_rows, key=lambda row: float(row["token_throughput_per_s"]))
    equivalence = activity_report.get("equivalence", {})
    return {
        "version": 1,
        "model": "decoder_attention_decode_score_multivalue_cluster_frontier_llama7b_v1",
        "decision": "shared_score_multivalue_cluster_measured_component_frontier_promoted",
        "inputs": {
            "prior_frontier_json": str(prior_frontier_json),
            "activity_power_json": str(activity_power_json),
            "source_schedule_json": schedule_source,
        },
        "schedule_contract": {
            "hidden_size": int(schedule["hidden_size"]),
            "attention_heads": int(schedule["attention_heads"]),
            "kv_heads": int(schedule["kv_heads"]),
            "head_dim": int(schedule["hidden_size"]) // int(schedule["attention_heads"]),
            "sequence_length": int(schedule["sequence_length"]),
            "layers": int(schedule["layers"]),
            "full_head_commands_per_layer": int(schedule["attention_heads"]),
            "full_head_command_cycles": command_cycles,
            "full_head_phase_cycles": phase_cycles,
            "sequence_sharding_supported": False,
        },
        "selected_cluster": {
            "candidate_id": best.get("candidate_id"),
            "flow_variant": best.get("flow_variant"),
            "ppa_metric": best["ppa_metric"],
            "activity_energy": energy,
        },
        "dense_qkv_tile": dense_tile,
        "precision": {
            "status": _EXPECTED_PRECISION_STATUS,
            "equivalence_pass": True,
            "decision": _EXPECTED_EQUIVALENCE_DECISION,
            "score_tensor_hash": str(equivalence["score_tensor_hash"]).strip(),
            "final_tensor_hash": str(equivalence["final_tensor_hash"]).strip(),
            "quality_change": "none_exact_integer_semantics_preserved",
        },
        "rows": rows,
        "pareto_rows": pareto_rows,
        "best_throughput_candidate": best_throughput,
        "promotion_status": "component_frontier_promoted_full_architecture_promotion_blocked",
        "remaining_abstractions": [
            (
                "Value memory is modeled as ready/no-stall with the measured one-cycle "
                "response contract."
            ),
            (
                "Producer, Q/K/V transport, NoC, HBM/DRAM, off-cluster value memory, "
                "and clock-tree composition are outside this frontier."
            ),
            "Dense QKV tile PPA is measured independently and composed by an area/schedule model.",
            "FakeRAM uses Nangate45 proxy LEF/Liberty views without SRAM compiler signoff.",
            "Score multiplier and shift derivation remain external to the cluster boundary.",
            (
                "Total token energy is incomplete; only activity-backed attention-cluster "
                "dynamic energy and service-window leakage are reported. Leakage outside "
                "the modeled cluster service windows is not included."
            ),
            (
                "Sequence sharding and cross-cluster head reduction are not implemented, "
                "so cluster count is capped at 32."
            ),
        ],
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    best = payload["best_throughput_candidate"]
    lines = [
        "# Llama7B shared-score multivalue cluster frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- best measured-component throughput: `{best['token_throughput_per_s']}` token/s",
        f"- best measured-component area: `{best['embodied_logic_plus_shared_sram_area_mm2']}` mm2",
        (
            "- attention-cluster modeled-service energy: "
            f"`{best['attention_cluster_modeled_service_energy_mj_per_token']}` mJ/token"
        ),
        (
            "- attention-cluster service-window leakage: "
            f"`{best['attention_cluster_service_window_leakage_energy_mj_per_token']}` mJ/token"
        ),
        "- total-token energy: `incomplete`",
        "",
        (
            "| candidate | clusters | waves/layer | QKV tiles | latency us | token/s | "
            "area mm2 | modeled service mJ/token |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['candidate_id']} | {row['cluster_count']} | "
            f"{row['cluster_waves_per_layer']} | {row['dense_qkv_tile_count']} | "
            f"{row['latency_us']} | {row['token_throughput_per_s']} | "
            f"{row['embodied_logic_plus_shared_sram_area_mm2']} | "
            f"{row['attention_cluster_modeled_service_energy_mj_per_token']} |"
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-frontier-json", type=Path, required=True)
    parser.add_argument("--activity-power-json", type=Path, required=True)
    parser.add_argument("--cluster-counts", default="1,2,4,8,16,32")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        prior_frontier_json=args.prior_frontier_json,
        activity_power_json=args.activity_power_json,
        cluster_counts=[int(value) for value in args.cluster_counts.split(",")],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

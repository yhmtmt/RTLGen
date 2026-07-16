#!/usr/bin/env python3
"""Recost the Llama7B proxy with the measured complete GQA8 group."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterator


JsonDict = dict[str, Any]
_QUERY_HEADS_PER_KV = 8
_GROUP_ACTIVITY_MODEL = "decoder_attention_decode_score_multivalue_gqa_group_activity_power_v1"
_GROUP_ACTIVITY_DECISION = "activity_backed_gqa_group_power_measured"
_SUPPORTED_GROUP_COUNTS = {1, 2, 4}


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _linked_path(link: str, frontier_path: Path) -> Path:
    candidate_paths = []
    linked_path = Path(link)
    if linked_path.is_absolute():
        candidate_paths.append(linked_path)
    else:
        candidate_paths.extend((frontier_path.parent / linked_path, Path.cwd() / linked_path))
    for candidate in candidate_paths:
        if candidate.is_file():
            return candidate
    raise ValueError(f"linked prior frontier does not exist: {link}")


def _frontier_chain(frontier: JsonDict, frontier_path: Path) -> Iterator[tuple[JsonDict, Path]]:
    current = frontier
    current_path = frontier_path
    visited: set[Path] = set()
    while True:
        resolved_path = current_path.resolve()
        if resolved_path in visited:
            raise ValueError("prior frontier linkage contains a cycle")
        visited.add(resolved_path)
        yield current, current_path
        inputs = current.get("inputs")
        linked = inputs.get("prior_frontier_json") if isinstance(inputs, dict) else None
        if not isinstance(linked, str) or not linked:
            return
        current_path = _linked_path(linked, current_path)
        current = _load(current_path)


def _source_schedule(frontier: JsonDict, frontier_path: Path) -> tuple[JsonDict, str]:
    for candidate, candidate_path in _frontier_chain(frontier, frontier_path):
        schedule = candidate.get("source_schedule")
        if isinstance(schedule, dict):
            return schedule, str(candidate_path)
    raise ValueError("prior frontier chain lacks source_schedule")


def _prior_measurement(
    frontier: JsonDict, frontier_path: Path, key: str
) -> tuple[JsonDict, str]:
    for candidate, candidate_path in _frontier_chain(frontier, frontier_path):
        measurement = candidate.get(key)
        if isinstance(measurement, dict):
            return measurement, str(candidate_path)
    raise ValueError(f"prior frontier chain lacks measured {key} evidence")


def _positive(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def _validate_equivalence(equivalence: Any) -> JsonDict:
    if not isinstance(equivalence, dict):
        raise ValueError("group activity report lacks full merged equivalence")
    expected_hash = equivalence.get("expected_group_result_sha256")
    observed_hash = equivalence.get("observed_group_result_sha256")
    if not (
        equivalence.get("equivalence_pass") is True
        and equivalence.get("decision") == "llama7b_gqa8_shared_kv_equivalence_pass"
        and int(equivalence.get("query_heads_per_kv", 0)) == _QUERY_HEADS_PER_KV
        and isinstance(expected_hash, str)
        and bool(expected_hash)
        and expected_hash == observed_hash
    ):
        raise ValueError("full merged GQA8 equivalence did not pass")
    return {
        "equivalence_pass": True,
        "decision": equivalence["decision"],
        "semantic_profile": equivalence.get("semantic_profile"),
        "query_heads_per_kv": _QUERY_HEADS_PER_KV,
        "expected_group_result_sha256": expected_hash,
        "observed_group_result_sha256": observed_hash,
    }


def _selected_group(activity_report: JsonDict) -> tuple[JsonDict, JsonDict, float, int, float, JsonDict]:
    if activity_report.get("model") != _GROUP_ACTIVITY_MODEL:
        raise ValueError("group activity-power report model contract failed")
    if activity_report.get("decision") != _GROUP_ACTIVITY_DECISION:
        raise ValueError("group activity-power report decision contract failed")
    if activity_report.get("promotion_gate_pass") is not True:
        raise ValueError("group activity-power promotion gate did not pass")
    best = activity_report.get("best")
    if not isinstance(best, dict):
        raise ValueError("group activity report lacks a promoted best candidate")
    ppa_metric = best.get("ppa_metric")
    activity_power = best.get("activity_power")
    if not isinstance(ppa_metric, dict) or not isinstance(activity_power, dict):
        raise ValueError("group activity report lacks the promoted best PPA/activity evidence")
    if best.get("status") != "activity_backed":
        raise ValueError("promoted group candidate is not activity-backed")
    if activity_report.get("best_candidate_id") != best.get("candidate_id"):
        raise ValueError("group activity report best-candidate identity is inconsistent")
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError("promoted group activity power is not gated")
    direct_energy = _positive(
        best.get("direct_group_full_context_energy_j"),
        "direct group full-context energy",
    )
    measured_energy = _positive(
        activity_power.get("full_context_energy_j"),
        "group activity full-context energy",
    )
    if not math.isclose(direct_energy, measured_energy, rel_tol=1.0e-9, abs_tol=1.0e-15):
        raise ValueError("direct group energy does not match activity energy")
    raw_full_context_cycles = _positive(
        activity_power.get("full_context_cycles"), "group full-context cycles"
    )
    full_context_cycles = int(raw_full_context_cycles)
    if raw_full_context_cycles != full_context_cycles:
        raise ValueError("group full-context cycles must be an integer")
    activity_clock_ns = _positive(
        activity_power.get(
            "clock_period_ns",
            activity_report.get("activity_contract", {}).get("clock_period_ns"),
        ),
        "activity clock",
    )
    contract = activity_report.get("activity_contract")
    if not isinstance(contract, dict) or int(contract.get("query_heads_per_kv", 0)) != _QUERY_HEADS_PER_KV:
        raise ValueError("group activity report is not GQA8")
    if activity_report.get("energy_scope") != "one GQA8 group full-context decode attention command":
        raise ValueError("group activity report energy scope is incompatible")
    equivalence = _validate_equivalence(activity_report.get("equivalence"))
    return best, ppa_metric, direct_energy, full_context_cycles, activity_clock_ns, equivalence


def _row(
    *,
    group_count: int,
    schedule: JsonDict,
    group_metric: JsonDict,
    group_cycles: int,
    activity_clock_ns: float,
    group_energy_j: float,
    dense_tile: JsonDict,
) -> JsonDict:
    attention_heads = int(schedule["attention_heads"])
    kv_heads = int(schedule["kv_heads"])
    layers = int(schedule["layers"])
    hidden = int(schedule["hidden_size"])
    head_dim = hidden // attention_heads
    if group_count < 1 or group_count > kv_heads:
        raise ValueError(f"group count must be in [1, {kv_heads}]")
    group_area_um2 = _positive(group_metric["instance_area_um2"], "group area")
    dense_area_um2 = _positive(dense_tile["area_um2"], "dense QKV tile area")
    dense_macs = _positive(dense_tile["effective_macs_per_cycle"], "dense QKV MAC/cycle")
    budget_um2 = _positive(schedule["compute_budget_um2"], "compute budget")
    logical_groups = kv_heads
    group_total_um2 = group_count * group_area_um2
    qkv_useful_limit = hidden // 8 + 2 * kv_heads * head_dim // 8
    dense_count = min(
        qkv_useful_limit,
        max(0, math.floor((budget_um2 - group_total_um2) / dense_area_um2)),
    )
    area_fit = dense_count > 0 and group_total_um2 + dense_count * dense_area_um2 <= budget_um2
    qkv_work = hidden**2 + 2 * hidden * kv_heads * head_dim
    qkv_cycles = math.ceil(qkv_work / (dense_count * dense_macs)) if dense_count else None
    waves = math.ceil(logical_groups / group_count)
    attention_cycles = waves * group_cycles
    fixed_cycles = int(schedule.get("command_dispatch_cycles", 0)) + int(
        schedule.get("kv_write_cycles", 0)
    )
    layer_cycles = qkv_cycles + attention_cycles + fixed_cycles if qkv_cycles is not None else None
    clock_ns = max(_positive(schedule["clock_ns"], "schedule clock"), activity_clock_ns)
    total_cycles = layer_cycles * layers if layer_cycles is not None else None
    latency_us = total_cycles * clock_ns / 1000.0 if total_cycles is not None else None
    noncompute_logic_um2 = float(schedule["logic_area_used_um2"]) - float(
        schedule["compute_area_um2"]
    )
    logic_area_um2 = noncompute_logic_um2 + group_total_um2 + dense_count * dense_area_um2
    shared_sram_um2 = float(schedule.get("measured_shared_sram_used_area_um2", 0.0)) + float(
        schedule.get("measured_tile_local_sram_area_um2", 0.0)
    )
    component_energy_j = logical_groups * layers * group_energy_j
    return {
        "candidate_id": f"decode_score_multivalue_gqa_group_g{group_count}",
        "group_count": group_count,
        "logical_groups_per_layer": logical_groups,
        "group_waves_per_layer": waves,
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
        "group_area_mm2": round(group_total_um2 / 1.0e6, 9),
        "dense_qkv_area_mm2": round(dense_count * dense_area_um2 / 1.0e6, 9),
        "compute_budget_slack_mm2": round(
            (budget_um2 - group_total_um2 - dense_count * dense_area_um2) / 1.0e6, 9
        ),
        "logic_area_mm2": round(logic_area_um2 / 1.0e6, 9),
        "embodied_logic_plus_shared_sram_area_mm2": round(
            (logic_area_um2 + shared_sram_um2) / 1.0e6, 9
        ),
        "compute_budget_area_fit": area_fit,
        "group_critical_path_ns": _positive(group_metric["critical_path_ns"], "group path"),
        "timing_feasible": _positive(group_metric["critical_path_ns"], "group path") <= clock_ns,
        "gqa_group_component_energy_j_per_token": component_energy_j,
        "gqa_group_component_energy_mj_per_token": component_energy_j * 1.0e3,
        "energy_scope": (
            "GQA8 group component only: 4 logical groups/layer times layers; "
            "not total-token energy"
        ),
        "energy_status": "activity_backed_gqa_group_component_only_total_token_energy_incomplete",
    }


def _pareto(rows: list[JsonDict]) -> list[JsonDict]:
    feasible = [
        row
        for row in rows
        if row["compute_budget_area_fit"]
        and row["timing_feasible"]
        and row["latency_us"] is not None
    ]
    result = []
    for row in feasible:
        dominated = any(
            other is not row
            and float(other["latency_us"]) <= float(row["latency_us"])
            and float(other["embodied_logic_plus_shared_sram_area_mm2"])
            <= float(row["embodied_logic_plus_shared_sram_area_mm2"])
            and float(other["gqa_group_component_energy_mj_per_token"])
            <= float(row["gqa_group_component_energy_mj_per_token"])
            and (
                float(other["latency_us"]) < float(row["latency_us"])
                or float(other["embodied_logic_plus_shared_sram_area_mm2"])
                < float(row["embodied_logic_plus_shared_sram_area_mm2"])
                or float(other["gqa_group_component_energy_mj_per_token"])
                < float(row["gqa_group_component_energy_mj_per_token"])
            )
            for other in feasible
        )
        if not dominated:
            result.append(row)
    return result


def _prior_comparison(prior: JsonDict, best: JsonDict) -> JsonDict:
    prior_best = prior.get("best_throughput_candidate")
    if not isinstance(prior_best, dict):
        return {"available": False, "reason": "prior frontier has no best throughput candidate"}
    prior_throughput = prior_best.get("token_throughput_per_s")
    if prior_throughput is None:
        return {"available": False, "reason": "prior best lacks token throughput"}
    prior_throughput = float(prior_throughput)
    current_throughput = float(best["token_throughput_per_s"])
    return {
        "available": True,
        "prior_candidate_id": prior_best.get("candidate_id"),
        "prior_token_throughput_per_s": prior_throughput,
        "best_group_token_throughput_per_s": current_throughput,
        "throughput_delta_per_s": current_throughput - prior_throughput,
        "throughput_ratio": current_throughput / prior_throughput if prior_throughput else None,
    }


def build_report(
    *, prior_frontier_json: Path, activity_power_json: Path, group_counts: list[int]
) -> JsonDict:
    prior = _load(prior_frontier_json)
    activity_report = _load(activity_power_json)
    if not group_counts:
        raise ValueError("at least one group count is required")
    if len(group_counts) != len(set(group_counts)):
        raise ValueError("group counts must be unique")
    unsupported = set(group_counts) - _SUPPORTED_GROUP_COUNTS
    if unsupported:
        raise ValueError(f"unsupported group counts: {sorted(unsupported)}")
    schedule, schedule_source = _source_schedule(prior, prior_frontier_json)
    dense_tile, dense_tile_source = _prior_measurement(prior, prior_frontier_json, "dense_qkv_tile")
    if (
        int(schedule["hidden_size"]) != 4096
        or int(schedule["attention_heads"]) != 32
        or int(schedule["kv_heads"]) != 4
        or int(schedule["attention_heads"])
        != int(schedule["kv_heads"]) * _QUERY_HEADS_PER_KV
    ):
        raise ValueError("frontier is not the expected Llama7B 4096D/32Q-head/4KV-head schedule")
    best, group_metric, group_energy_j, group_cycles, activity_clock_ns, equivalence = _selected_group(
        activity_report
    )
    rows = [
        _row(
            group_count=count,
            schedule=schedule,
            group_metric=group_metric,
            group_cycles=group_cycles,
            activity_clock_ns=activity_clock_ns,
            group_energy_j=group_energy_j,
            dense_tile=dense_tile,
        )
        for count in group_counts
    ]
    pareto_rows = _pareto(rows)
    if not pareto_rows:
        raise ValueError("no feasible GQA8 group frontier row")
    best_throughput = max(pareto_rows, key=lambda row: float(row["token_throughput_per_s"]))
    return {
        "version": 1,
        "model": "decoder_attention_decode_score_multivalue_gqa_group_frontier_llama7b_v1",
        "decision": "measured_complete_gqa8_group_component_frontier_promoted",
        "inputs": {
            "prior_frontier_json": str(prior_frontier_json),
            "group_activity_power_json": str(activity_power_json),
            "source_schedule_json": schedule_source,
            "dense_qkv_tile_source_json": dense_tile_source,
        },
        "schedule_contract": {
            "hidden_size": int(schedule["hidden_size"]),
            "attention_heads": int(schedule["attention_heads"]),
            "kv_heads": int(schedule["kv_heads"]),
            "query_heads_per_kv": _QUERY_HEADS_PER_KV,
            "head_dim": int(schedule["hidden_size"]) // int(schedule["attention_heads"]),
            "sequence_length": int(schedule["sequence_length"]),
            "layers": int(schedule["layers"]),
            "logical_groups_per_layer": int(schedule["kv_heads"]),
            "group_full_context_cycles": group_cycles,
            "sequence_sharding_supported": False,
        },
        "selected_group": {
            "candidate_id": best.get("candidate_id"),
            "flow_variant": best.get("flow_variant"),
            "ppa_metric": group_metric,
            "direct_group_full_context_energy_j": group_energy_j,
            "activity_power": best["activity_power"],
        },
        "dense_qkv_tile": dense_tile,
        "precision": {
            "status": "exact",
            "equivalence_pass": equivalence["equivalence_pass"],
            "decision": equivalence["decision"],
            "semantic_profile": equivalence["semantic_profile"],
            "query_heads_per_kv": _QUERY_HEADS_PER_KV,
            "expected_group_result_sha256": equivalence["expected_group_result_sha256"],
            "observed_group_result_sha256": equivalence["observed_group_result_sha256"],
            "quality_change": "none_exact_integer_semantics_preserved",
        },
        "rows": rows,
        "pareto_rows": pareto_rows,
        "best_throughput_candidate": best_throughput,
        "comparison_to_prior_best": _prior_comparison(prior, best_throughput),
        "promotion_status": "component_frontier_promoted_full_architecture_promotion_blocked",
        "remaining_abstractions": [
            "Multi-group PPA uses linear scaling of the measured complete GQA8 group, not array-level PNR.",
            "Off-group value memory, NoC, HBM/DRAM, and clock-tree composition are outside this frontier.",
            "FakeRAM uses Nangate45 proxy LEF/Liberty views without SRAM compiler signoff.",
            "Total-token energy is incomplete; only the activity-backed GQA8 group component is reported.",
            "No group flow pairing with prior single-cluster or cluster-frontier variants is inferred.",
        ],
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    best = payload["best_throughput_candidate"]
    comparison = payload["comparison_to_prior_best"]
    lines = [
        "# Llama7B GQA8 group frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- best measured-component throughput: `{best['token_throughput_per_s']}` token/s",
        f"- best measured-component area: `{best['embodied_logic_plus_shared_sram_area_mm2']}` mm2",
        f"- GQA8 group-component energy: `{best['gqa_group_component_energy_mj_per_token']}` mJ/token",
        "- total-token energy: `incomplete`",
    ]
    if comparison["available"]:
        lines.append(
            f"- throughput delta vs prior best: `{comparison['throughput_delta_per_s']}` token/s"
        )
    else:
        lines.append("- prior-best comparison: `unavailable`")
    lines.extend(
        [
            "",
            "| candidate | groups | logical groups/layer | waves/layer | QKV tiles | latency us | token/s | area mm2 | group-component mJ/token |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| {row['candidate_id']} | {row['group_count']} | {row['logical_groups_per_layer']} | "
            f"{row['group_waves_per_layer']} | {row['dense_qkv_tile_count']} | {row['latency_us']} | "
            f"{row['token_throughput_per_s']} | {row['embodied_logic_plus_shared_sram_area_mm2']} | "
            f"{row['gqa_group_component_energy_mj_per_token']} |"
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-frontier-json", type=Path, required=True)
    parser.add_argument("--group-activity-power-json", type=Path, required=True)
    parser.add_argument("--group-counts", default="1,2,4")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    group_counts = [int(value.strip()) for value in args.group_counts.split(",") if value.strip()]
    payload = build_report(
        prior_frontier_json=args.prior_frontier_json,
        activity_power_json=args.group_activity_power_json,
        group_counts=group_counts,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

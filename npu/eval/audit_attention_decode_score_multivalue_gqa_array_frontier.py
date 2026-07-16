#!/usr/bin/env python3
"""Recost the Llama7B GQA frontier with directly measured GQA arrays."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Iterator, Mapping


JsonDict = dict[str, Any]
_QUERY_HEADS_PER_KV = 8
_GROUP_COUNTS = (1, 2, 4)
_PRIOR_MODEL = "decoder_attention_decode_score_multivalue_gqa_group_frontier_llama7b_v1"
_PRIOR_DECISION = "measured_complete_gqa8_group_component_frontier_promoted"
_EQUIVALENCE_MODEL = "llama7b_gqa8_multigroup_array_compositional_equivalence_v1"
_EQUIVALENCE_DECISION = "llama7b_gqa8_multigroup_array_equivalence_pass"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _linked_path(link: str, frontier_path: Path) -> Path:
    linked = Path(link)
    candidates = [linked] if linked.is_absolute() else [frontier_path.parent / linked, Path.cwd() / linked]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ValueError(f"linked prior frontier does not exist: {link}")


def _frontier_chain(frontier: JsonDict, frontier_path: Path) -> Iterator[tuple[JsonDict, Path]]:
    current, current_path = frontier, frontier_path
    visited: set[Path] = set()
    while True:
        resolved = current_path.resolve()
        if resolved in visited:
            raise ValueError("prior frontier linkage contains a cycle")
        visited.add(resolved)
        yield current, current_path
        inputs = current.get("inputs")
        link = inputs.get("prior_frontier_json") if isinstance(inputs, dict) else None
        if not isinstance(link, str) or not link:
            return
        current_path = _linked_path(link, current_path)
        current = _load(current_path)


def _source_evidence(frontier: JsonDict, frontier_path: Path, key: str) -> tuple[JsonDict, str]:
    for candidate, candidate_path in _frontier_chain(frontier, frontier_path):
        value = candidate.get(key)
        if isinstance(value, dict):
            return value, str(candidate_path)
    raise ValueError(f"prior frontier chain lacks {key}")


def _positive(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite and positive") from exc
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return result


def _finite_positive(value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError("value must be finite and positive")
    return result


def _validate_prior(prior: JsonDict) -> JsonDict:
    if prior.get("model") != _PRIOR_MODEL:
        raise ValueError("prior frontier model contract failed")
    if prior.get("decision") != _PRIOR_DECISION:
        raise ValueError("prior frontier decision contract failed")
    precision = prior.get("precision")
    if not isinstance(precision, dict) or precision.get("status") != "exact":
        raise ValueError("prior frontier precision contract failed")
    return {
        "model": prior["model"],
        "decision": prior["decision"],
        "precision_status": precision["status"],
        "precision": precision,
    }


def _validate_equivalence(equivalence: JsonDict) -> JsonDict:
    if (
        equivalence.get("model") != _EQUIVALENCE_MODEL
        or equivalence.get("decision") != _EQUIVALENCE_DECISION
        or equivalence.get("equivalence_pass") is not True
        or equivalence.get("precision_status") != "exact"
        or equivalence.get("measured_group_counts") != list(_GROUP_COUNTS)
    ):
        raise ValueError("array equivalence model/decision/precision/count contract failed")
    return {
        "model": equivalence["model"],
        "decision": equivalence["decision"],
        "equivalence_pass": True,
        "precision_status": equivalence["precision_status"],
        "semantic_profile": equivalence.get("semantic_profile"),
        "query_heads_per_kv": equivalence.get("query_heads_per_kv"),
        "measured_group_counts": list(_GROUP_COUNTS),
        "array_configs": equivalence.get("array_configs"),
    }


def _first_value(row: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return value
    return None


def _parse_metrics_row(raw: Mapping[str, Any], *, metrics_path: Path, count: int, line: int) -> JsonDict:
    evidence: JsonDict = {
        "metrics_path": str(metrics_path),
        "csv_line": line,
        "requested_group_count": count,
        "raw": dict(raw),
        "status": raw.get("status", ""),
        "design": raw.get("design"),
        "platform": raw.get("platform"),
        "config_hash": raw.get("config_hash"),
        "param_hash": raw.get("param_hash"),
        "result_path": raw.get("result_path"),
    }
    try:
        params_text = raw.get("params_json")
        params = json.loads(params_text) if isinstance(params_text, str) else None
        if not isinstance(params, dict):
            raise ValueError("params_json is not an object")
        evidence["params"] = params
    except (TypeError, json.JSONDecodeError, ValueError) as exc:
        evidence.update({"accepted": False, "reason": f"invalid params_json: {exc}"})
        return evidence

    params = evidence["params"]
    evidence.update(
        {
            "flow_variant": _first_value(raw, ("flow_variant",)) or params.get("FLOW_VARIANT"),
            "die_area": _first_value(raw, ("die_area",)) or params.get("DIE_AREA"),
            "core_area": _first_value(raw, ("core_area",)) or params.get("CORE_AREA"),
            "core_utilization": _first_value(raw, ("core_utilization",)) or params.get("CORE_UTILIZATION"),
        }
    )
    status = str(raw.get("status") or "").strip().lower()
    if status != "ok":
        evidence.update({"accepted": False, "reason": f"status is {status or 'missing'}, not ok"})
        return evidence

    try:
        configured_clock = _positive(params.get("CLOCK_PERIOD"), "configured CLOCK_PERIOD")
        critical_path = _positive(
            _first_value(raw, ("critical_path_ns", "critical_path")), "critical path"
        )
        instance_value = _first_value(raw, ("instance_area_um2", "instance_area"))
        instance_area = _positive(instance_value, "instance area")
        row_group = params.get("GROUP_COUNT", params.get("group_count"))
        if row_group is not None and int(row_group) != count:
            raise ValueError(f"params group_count {row_group} does not match requested {count}")
        if critical_path > configured_clock:
            raise ValueError(
                f"critical path {critical_path} ns exceeds configured CLOCK_PERIOD {configured_clock} ns"
            )
    except (TypeError, ValueError, OverflowError) as exc:
        evidence.update({"accepted": False, "reason": str(exc)})
        return evidence

    evidence.update(
        {
            "accepted": True,
            "reason": "timing-feasible direct metrics row",
            "configured_clock_period_ns": configured_clock,
            "critical_path_ns": critical_path,
            "instance_area_um2": instance_area,
        }
    )
    return evidence


def _read_metrics(path: Path, count: int) -> list[JsonDict]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"metrics CSV has no header: {path}")
        return [_parse_metrics_row(row, metrics_path=path, count=count, line=index) for index, row in enumerate(reader, 2)]


def _prior_rows_by_group(prior: JsonDict) -> dict[int, JsonDict]:
    rows = prior.get("rows")
    if not isinstance(rows, list):
        raise ValueError("prior frontier lacks rows")
    result: dict[int, JsonDict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            count = int(row["group_count"])
        except (KeyError, TypeError, ValueError):
            continue
        if count in result:
            raise ValueError(f"prior frontier has duplicate group_count {count}")
        result[count] = row
    missing = set(_GROUP_COUNTS) - set(result)
    if missing:
        raise ValueError(f"prior frontier lacks rows for group counts {sorted(missing)}")
    return result


def _recost_candidate(
    *, group_count: int, schedule: JsonDict, dense_tile: JsonDict, prior_row: JsonDict, metric: JsonDict
) -> JsonDict:
    hidden = int(schedule["hidden_size"])
    attention_heads = int(schedule["attention_heads"])
    kv_heads = int(schedule["kv_heads"])
    layers = int(schedule["layers"])
    head_dim = hidden // attention_heads
    group_cycles_raw = schedule.get("group_full_context_cycles")
    if group_cycles_raw is None:
        raise ValueError("schedule lacks group_full_context_cycles")
    group_cycles = int(group_cycles_raw)
    if group_cycles <= 0 or group_cycles != float(group_cycles_raw):
        raise ValueError("group_full_context_cycles must be a positive integer")
    direct_area = _positive(metric["instance_area_um2"], "direct array instance area")
    dense_area = _positive(dense_tile["area_um2"], "dense QKV tile area")
    dense_macs = _positive(dense_tile["effective_macs_per_cycle"], "dense QKV MAC/cycle")
    budget = _positive(schedule["compute_budget_um2"], "compute budget")
    useful_limit = hidden // 8 + 2 * kv_heads * head_dim // 8
    dense_count = min(useful_limit, max(0, math.floor((budget - direct_area) / dense_area)))
    area_fit = dense_count > 0 and direct_area + dense_count * dense_area <= budget
    qkv_work = hidden**2 + 2 * hidden * kv_heads * head_dim
    qkv_cycles = math.ceil(qkv_work / (dense_count * dense_macs)) if dense_count else None
    waves = math.ceil(kv_heads / group_count)
    attention_cycles = waves * group_cycles
    fixed_cycles = int(schedule.get("command_dispatch_cycles", 0)) + int(schedule.get("kv_write_cycles", 0))
    layer_cycles = qkv_cycles + attention_cycles + fixed_cycles if qkv_cycles is not None else None
    source_clock = _positive(schedule["clock_ns"], "source schedule clock")
    ppa_clock = _positive(metric["configured_clock_period_ns"], "configured CLOCK_PERIOD")
    effective_clock = max(source_clock, ppa_clock)
    total_cycles = layer_cycles * layers if layer_cycles is not None else None
    latency = total_cycles * effective_clock / 1000.0 if total_cycles is not None else None
    noncompute_logic = float(schedule["logic_area_used_um2"]) - float(schedule["compute_area_um2"])
    shared_sram = float(schedule.get("measured_shared_sram_used_area_um2", 0.0)) + float(
        schedule.get("measured_tile_local_sram_area_um2", 0.0)
    )
    prior_energy = prior_row.get("gqa_group_component_energy_mj_per_token")
    if prior_energy is None and prior_row.get("gqa_group_component_energy_j_per_token") is not None:
        prior_energy = float(prior_row["gqa_group_component_energy_j_per_token"]) * 1.0e3
    prior_energy = _positive(prior_energy, "prior compositional group-component energy")
    logic_area = noncompute_logic + direct_area + dense_count * dense_area

    prior_area = float(prior_row["group_area_mm2"]) * 1.0e6
    prior_latency = _positive(prior_row["latency_us"], "prior group-composed latency")
    prior_throughput = _positive(prior_row["token_throughput_per_s"], "prior group-composed throughput")
    prior_clock = _positive(prior_row["clock_ns"], "prior group-composed clock")
    return {
        "candidate_id": f"decode_score_multivalue_gqa_array_g{group_count}_{metric['param_hash'] or 'metric'}",
        "group_count": group_count,
        "dense_qkv_tile_count": dense_count,
        "dense_qkv_useful_parallelism_limit": useful_limit,
        "qkv_work": qkv_work,
        "qkv_cycles": qkv_cycles,
        "logical_groups_per_layer": kv_heads,
        "group_waves_per_layer": waves,
        "attention_cycles": attention_cycles,
        "fixed_cycles": fixed_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "critical_path_ns": metric["critical_path_ns"],
        "direct_array_critical_path_ns": metric["critical_path_ns"],
        "configured_clock_period_ns": ppa_clock,
        "source_schedule_clock_ns": source_clock,
        "clock_ns": effective_clock,
        "clock_provenance": "max(source_schedule.clock_ns, metrics.params_json.CLOCK_PERIOD)",
        "latency_us": round(latency, 6) if latency is not None else None,
        "token_throughput_per_s": round(1.0e6 / latency, 12) if latency else None,
        "direct_array_instance_area_um2": direct_area,
        "direct_array_instance_area_mm2": round(direct_area / 1.0e6, 9),
        "noncompute_logic_area_um2": noncompute_logic,
        "measured_shared_sram_used_area_um2": float(schedule.get("measured_shared_sram_used_area_um2", 0.0)),
        "measured_tile_local_sram_area_um2": float(schedule.get("measured_tile_local_sram_area_um2", 0.0)),
        "measured_shared_plus_local_sram_area_um2": shared_sram,
        "dense_qkv_area_mm2": round(dense_count * dense_area / 1.0e6, 9),
        "compute_budget_slack_mm2": round((budget - direct_area - dense_count * dense_area) / 1.0e6, 9),
        "logic_area_mm2": round(logic_area / 1.0e6, 9),
        "embodied_logic_plus_shared_sram_area_mm2": round((logic_area + shared_sram) / 1.0e6, 9),
        "direct_embodied_logic_plus_shared_sram_area_mm2": round((logic_area + shared_sram) / 1.0e6, 9),
        "compute_budget_area_fit": area_fit,
        "timing_feasible": True,
        "recost_status": "accepted" if area_fit else "compute_budget_infeasible",
        "prior_compositional_gqa_group_component_energy_mj_per_token": prior_energy,
        "energy_scope": "prior GQA8 group-component activity evidence only; not direct array activity and not total-token energy",
        "energy_status": "NOT_direct_array_activity_NOT_total_token_energy_prior_compositional_evidence",
        "metrics_provenance": {
            "metrics_path": metric["metrics_path"],
            "csv_line": metric["csv_line"],
            "config_hash": metric["config_hash"],
            "param_hash": metric["param_hash"],
            "flow_variant": metric["flow_variant"],
            "platform": metric["platform"],
            "die_area": metric["die_area"],
            "core_area": metric["core_area"],
            "core_utilization": metric["core_utilization"],
            "critical_path_ns": metric["critical_path_ns"],
            "instance_area_um2": direct_area,
            "configured_clock_period_ns": ppa_clock,
            "params_json": metric["params"],
        },
        "prior_group_composed": {
            "candidate_id": prior_row.get("candidate_id"),
            "instance_area_um2": prior_area,
            "latency_us": prior_latency,
            "token_throughput_per_s": prior_throughput,
            "clock_ns": prior_clock,
            "clock_provenance": "prior group frontier max(source schedule clock, group activity clock)",
        },
        "direct_vs_prior_compositional_delta": {
            "instance_area_um2": direct_area - prior_area,
            "latency_us": (latency - prior_latency) if latency is not None else None,
            "throughput_per_s": (1.0e6 / latency - prior_throughput) if latency else None,
            "clock_ns": effective_clock - prior_clock,
            "clock_provenance": {
                "direct": "max(source schedule clock, direct metrics configured CLOCK_PERIOD)",
                "prior": "prior group frontier effective clock, including group activity clock",
                "differing_clock_sources": True,
            },
        },
    }


def _pareto(rows: list[JsonDict]) -> list[JsonDict]:
    feasible = [
        row for row in rows
        if row.get("compute_budget_area_fit") and row.get("timing_feasible") and row.get("latency_us") is not None
    ]
    energy_key = "prior_compositional_gqa_group_component_energy_mj_per_token"
    result: list[JsonDict] = []
    for row in feasible:
        dominated = any(
            other is not row
            and float(other["latency_us"]) <= float(row["latency_us"])
            and float(other["embodied_logic_plus_shared_sram_area_mm2"]) <= float(row["embodied_logic_plus_shared_sram_area_mm2"])
            and float(other[energy_key]) <= float(row[energy_key])
            and (
                float(other["latency_us"]) < float(row["latency_us"])
                or float(other["embodied_logic_plus_shared_sram_area_mm2"]) < float(row["embodied_logic_plus_shared_sram_area_mm2"])
                or float(other[energy_key]) < float(row[energy_key])
            )
            for other in feasible
        )
        if not dominated:
            result.append(row)
    return result


def build_report(
    *, prior_frontier_json: Path, array_equivalence_json: Path, array_metrics: Mapping[int, Path]
) -> JsonDict:
    if set(array_metrics) != set(_GROUP_COUNTS):
        raise ValueError(f"array metrics must cover exact group counts {list(_GROUP_COUNTS)}")
    prior = _load(prior_frontier_json)
    equivalence = _validate_equivalence(_load(array_equivalence_json))
    prior_contract = _validate_prior(prior)
    schedule, schedule_source = _source_evidence(prior, prior_frontier_json, "source_schedule")
    dense_tile, dense_source = _source_evidence(prior, prior_frontier_json, "dense_qkv_tile")
    if (
        int(schedule.get("hidden_size", 0)) != 4096
        or int(schedule.get("attention_heads", 0)) != 32
        or int(schedule.get("kv_heads", 0)) != 4
        or int(schedule.get("layers", 0)) != 32
        or int(schedule["attention_heads"]) != int(schedule["kv_heads"]) * _QUERY_HEADS_PER_KV
    ):
        raise ValueError("frontier is not the expected Llama7B 4096D/32Q-head/4KV-head/32-layer schedule")
    schedule_contract = prior.get("schedule_contract")
    if not isinstance(schedule_contract, dict):
        raise ValueError("prior frontier lacks schedule_contract")
    group_cycles = schedule_contract.get("group_full_context_cycles")
    if group_cycles is None:
        group_cycles = schedule.get("group_full_context_cycles")
    schedule = dict(schedule)
    schedule["group_full_context_cycles"] = group_cycles
    prior_rows = _prior_rows_by_group(prior)

    raw_rows: list[JsonDict] = []
    candidates: list[JsonDict] = []
    for count in _GROUP_COUNTS:
        parsed = _read_metrics(Path(array_metrics[count]), count)
        for metric in parsed:
            raw_rows.append(metric)
            if not metric["accepted"]:
                continue
            try:
                candidate = _recost_candidate(
                    group_count=count,
                    schedule=schedule,
                    dense_tile=dense_tile,
                    prior_row=prior_rows[count],
                    metric=metric,
                )
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                metric["accepted"] = False
                metric["reason"] = f"recost rejected: {exc}"
                continue
            metric["recost_candidate_id"] = candidate["candidate_id"]
            candidates.append(candidate)
    pareto = _pareto(candidates)
    if not pareto:
        raise ValueError("no feasible direct GQA array frontier row")
    best = max(pareto, key=lambda row: float(row["token_throughput_per_s"]))
    prior_best = prior.get("best_throughput_candidate")
    prior_comparison = {
        "available": isinstance(prior_best, dict) and prior_best.get("token_throughput_per_s") is not None,
    }
    if prior_comparison["available"]:
        prior_comparison.update(
            {
                "prior_candidate_id": prior_best.get("candidate_id"),
                "prior_token_throughput_per_s": float(prior_best["token_throughput_per_s"]),
                "best_direct_array_token_throughput_per_s": best["token_throughput_per_s"],
                "throughput_delta_per_s": best["token_throughput_per_s"] - float(prior_best["token_throughput_per_s"]),
            }
        )
    return {
        "version": 1,
        "model": "decoder_attention_decode_score_multivalue_gqa_array_frontier_llama7b_v1",
        "decision": "direct_gqa_array_timing_area_frontier_promoted_energy_blocked",
        "inputs": {
            "prior_frontier_json": str(prior_frontier_json),
            "array_equivalence_json": str(array_equivalence_json),
            "array_metrics": {str(count): str(array_metrics[count]) for count in _GROUP_COUNTS},
            "source_schedule_json": schedule_source,
            "dense_qkv_tile_source_json": dense_source,
        },
        "prior_contract": prior_contract,
        "array_equivalence": equivalence,
        "schedule_contract": {
            "hidden_size": 4096,
            "attention_heads": 32,
            "kv_heads": 4,
            "query_heads_per_kv": _QUERY_HEADS_PER_KV,
            "head_dim": 128,
            "sequence_length": int(schedule["sequence_length"]),
            "layers": 32,
            "logical_groups_per_layer": 4,
            "group_full_context_cycles": int(group_cycles),
            "sequence_sharding_supported": False,
        },
        "dense_qkv_tile": dense_tile,
        "raw_metrics_evidence": raw_rows,
        "recost_candidates": candidates,
        "rows": candidates,
        "pareto_candidates": pareto,
        "pareto_rows": pareto,
        "best_throughput_candidate": best,
        "comparison_to_prior_best": prior_comparison,
        "per_group_direct_vs_prior_compositional_deltas": {
            str(count): [
                {
                    "candidate_id": row["candidate_id"],
                    **row["direct_vs_prior_compositional_delta"],
                }
                for row in candidates
                if row["group_count"] == count
            ]
            for count in _GROUP_COUNTS
        },
        "promotion_status": "direct array timing/area promoted but energy/full architecture blocked",
        "promotion": {
            "direct_array_timing": "promoted",
            "direct_array_area": "promoted",
            "direct_array_activity_energy": "blocked",
            "full_architecture": "blocked",
        },
        "remaining_abstractions": [
            "Direct array activity power is not measured.",
            "External value memory, NoC, and HBM are outside this frontier.",
            "SRAM compiler signoff is not available.",
            "Total-token energy is incomplete.",
            "No monolithic 32-cluster arithmetic simulation was run.",
        ],
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    best = payload["best_throughput_candidate"]
    lines = [
        "# Llama7B GQA8 Direct Array Frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promotion: `{payload['promotion_status']}`",
        f"- best throughput: `{best['token_throughput_per_s']}` token/s",
        "- energy: prior compositional group-component evidence only; direct activity and total-token energy are blocked",
        "",
        "## Raw Metrics Evidence",
        "",
        "| group | line | status | accepted | reason | metrics path | config hash | param hash | critical path ns | instance area um2 | clock ns |",
        "|---:|---:|---|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["raw_metrics_evidence"]:
        lines.append(
            f"| {row['requested_group_count']} | {row['csv_line']} | {row.get('status', '')} | {row['accepted']} | {row['reason']} | "
            f"{row['metrics_path']} | {row.get('config_hash', '')} | {row.get('param_hash', '')} | "
            f"{row.get('critical_path_ns', '')} | {row.get('instance_area_um2', '')} | {row.get('configured_clock_period_ns', '')} |"
        )
    lines.extend(
        [
            "",
            "## Recost Candidates",
            "",
            "| candidate | group | timing | area fit | latency us | throughput token/s | direct array area mm2 | embodied area mm2 | prior compositional energy mJ/token |",
            "|---|---:|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in payload["recost_candidates"]:
        lines.append(
            f"| {row['candidate_id']} | {row['group_count']} | {row['timing_feasible']} | {row['compute_budget_area_fit']} | "
            f"{row['latency_us']} | {row['token_throughput_per_s']} | {row['direct_array_instance_area_mm2']} | "
            f"{row['embodied_logic_plus_shared_sram_area_mm2']} | {row['prior_compositional_gqa_group_component_energy_mj_per_token']} |"
        )
    lines.extend(["", "## Pareto Candidates", ""])
    lines.extend(f"- `{row['candidate_id']}`" for row in payload["pareto_candidates"])
    lines.extend(["", "## Per-Group Direct vs Prior Compositional", "", "| group | area delta um2 | latency delta us | throughput delta token/s | clock delta ns |", "|---:|---:|---:|---:|---:|"])
    for count, deltas in payload["per_group_direct_vs_prior_compositional_deltas"].items():
        for delta in deltas:
            lines.append(f"| {count} | {delta['instance_area_um2']} | {delta['latency_us']} | {delta['throughput_per_s']} | {delta['clock_ns']} |")
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-frontier-json", type=Path, required=True)
    parser.add_argument("--array-equivalence-json", type=Path, required=True)
    parser.add_argument("--array-metrics", action="append", required=True, metavar="COUNT=PATH")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    metrics: dict[int, Path] = {}
    for item in args.array_metrics:
        if "=" not in item:
            parser.error("--array-metrics must be COUNT=PATH")
        count_text, path_text = item.split("=", 1)
        try:
            count = int(count_text)
        except ValueError:
            parser.error(f"invalid array metrics count: {count_text}")
        if count in metrics:
            parser.error(f"duplicate array metrics count: {count}")
        metrics[count] = Path(path_text)
    payload = build_report(
        prior_frontier_json=args.prior_frontier_json,
        array_equivalence_json=args.array_equivalence_json,
        array_metrics=metrics,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit direct routed power for timing-feasible GQA group implementations."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from npu.eval.generate_attention_decode_score_multivalue_gqa_group_activity import (
    generate_phase_activity,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report

JsonDict = dict[str, Any]
_GQA_HEADS = 8
_CLUSTER_ACTIVITY_MODEL = "decoder_attention_decode_score_multivalue_cluster_activity_power_v1"


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("expected a JSON object")
    return payload


def _params(row: JsonDict) -> JsonDict:
    try:
        payload = json.loads(str(row.get("params_json", "{}")))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid params_json for PPA row {row.get('param_hash')}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"params_json is not an object for PPA row {row.get('param_hash')}")
    return payload


def _metric_provenance(row: JsonDict, metrics_csv: Path) -> JsonDict:
    fields = (
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "instance_area_um2",
        "stdcell_area_um2",
        "stdcell_count",
        "core_area_um2",
        "utilization_pct",
        "flow_elapsed_seconds",
        "stage_elapsed_seconds",
        "params_json",
    )
    return {
        "metrics_csv": metrics_csv.name,
        **{field: row[field] for field in fields if str(row.get(field, "")).strip()},
    }


def _feasible_metrics(metrics_csv: Path, clock_period_ns: float) -> list[JsonDict]:
    with metrics_csv.open(newline="", encoding="utf-8") as handle:
        raw_rows = [dict(row) for row in csv.DictReader(handle)]
    selected: dict[str, JsonDict] = {}
    for row in raw_rows:
        if str(row.get("status", "")) != "ok":
            continue
        params = _params(row)
        row_clock = float(params.get("CLOCK_PERIOD", 0.0))
        critical_path = float(row.get("critical_path_ns") or math.inf)
        flow_variant = str(params.get("FLOW_VARIANT", "")).strip()
        if not flow_variant or abs(row_clock - clock_period_ns) > 1e-9:
            continue
        if not math.isfinite(critical_path) or critical_path > clock_period_ns:
            continue
        previous = selected.get(flow_variant)
        if previous is None or float(row.get("instance_area_um2") or math.inf) < float(
            previous.get("instance_area_um2") or math.inf
        ):
            selected[flow_variant] = row
    if not selected:
        raise ValueError(f"no status=ok timing-feasible {clock_period_ns:g} ns group rows")
    return sorted(
        selected.values(),
        key=lambda row: (
            float(row.get("die_area") or math.inf),
            float(row.get("instance_area_um2") or math.inf),
            float(row.get("critical_path_ns") or math.inf),
        ),
    )


def _sanitized_failure(exc: Exception) -> JsonDict:
    message = str(exc).splitlines()[0].strip()
    if "/" in message or "\\" in message:
        message = f"evaluator-local path failure during {type(exc).__name__}"
    return {"error_type": type(exc).__name__, "error_summary": message[:240]}


def _finite_positive(value: object, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite positive number") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be a finite positive number")
    return number


def _cluster_baseline(path: Path, clock_period_ns: float) -> JsonDict:
    payload = _load(path)
    if payload.get("model") not in {None, _CLUSTER_ACTIVITY_MODEL}:
        raise ValueError("cluster activity power report model contract failed")
    if payload.get("promotion_gate_pass") is not True:
        raise ValueError("cluster activity power report is not a promoted measured baseline")
    best = payload.get("best")
    if not isinstance(best, dict):
        raise ValueError("cluster activity power report best contract is missing")
    activity_power = best.get("activity_power")
    if not isinstance(activity_power, dict):
        raise ValueError("cluster activity power report best.activity_power contract is missing")
    if activity_power.get("promotion_gate_pass") is not True:
        raise ValueError("cluster best.activity_power is not promotion-gated")
    baseline_clock = activity_power.get("clock_period_ns")
    if baseline_clock is None:
        contract = payload.get("activity_contract")
        if isinstance(contract, dict):
            baseline_clock = contract.get("clock_period_ns")
    if baseline_clock is None:
        raise ValueError("cluster activity baseline is missing clock_period_ns")
    if abs(float(baseline_clock) - clock_period_ns) > 1e-9:
        raise ValueError("cluster activity baseline clock period does not match group audit")
    baseline_energy = _finite_positive(
        activity_power.get("full_context_energy_j"),
        "cluster best.activity_power.full_context_energy_j",
    )
    baseline_cycles = _finite_positive(
        activity_power.get("full_context_cycles"),
        "cluster best.activity_power.full_context_cycles",
    )
    return {
        "candidate_id": best.get("candidate_id"),
        "clock_period_ns": float(baseline_clock),
        "full_context_energy_j": baseline_energy,
        "full_context_cycles": int(baseline_cycles),
        "activity_power_model": activity_power.get("model"),
        "report_model": payload.get("model"),
    }


def _validate_gqa_equivalence(equivalence: JsonDict) -> JsonDict:
    if equivalence.get("equivalence_pass") is not True:
        raise ValueError("GQA8 shared-KV equivalence did not pass")
    heads = equivalence.get("query_heads_per_kv")
    if heads is not None and int(heads) != _GQA_HEADS:
        raise ValueError("equivalence report is not for GQA8")
    return {
        "equivalence_pass": True,
        "decision": equivalence.get("decision"),
        "semantic_profile": equivalence.get("semantic_profile"),
        "query_heads_per_kv": int(heads) if heads is not None else _GQA_HEADS,
        "expected_group_result_sha256": equivalence.get("expected_group_result_sha256"),
        "observed_group_result_sha256": equivalence.get("observed_group_result_sha256"),
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    lines = [
        "# GQA8 shared-score multivalue group activity power",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promoted candidates: `{payload['promoted_candidate_count']}`",
        f"- measured candidates: `{payload['candidate_count']}`",
        f"- energy scope: `{payload['energy_scope']}`",
        f"- independent-cluster upper-bound factor: `{payload['independent_cluster_upper_bound_factor']}x`",
        "",
        "| variant | path ns | instance mm2 | status | group energy J | 8x cluster bound J | bound |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for row in payload["candidates"]:
        metric = row["ppa_metric"]
        comparison = row.get("independent_cluster_upper_bound", {})
        lines.append(
            "| {variant} | {path_ns} | {area_mm2:.6f} | {status} | {energy} | {bound} | {passed} |".format(
                variant=row["flow_variant"],
                path_ns=metric.get("critical_path_ns"),
                area_mm2=float(metric.get("instance_area_um2", 0.0)) / 1.0e6,
                status=row["status"],
                energy=row.get("direct_group_full_context_energy_j"),
                bound=comparison.get("energy_j"),
                passed=comparison.get("pass"),
            )
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    *,
    config: Path,
    group_metrics_csv: Path,
    cluster_activity_power_json: Path,
    equivalence_json: Path,
    group_orfs_design_config: Path,
    clock_period_ns: float,
    activity_dir: Path,
) -> JsonDict:
    equivalence = _validate_gqa_equivalence(_load(equivalence_json))
    cluster_baseline = _cluster_baseline(cluster_activity_power_json, clock_period_ns)
    activity_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "score_fill.vcd",
        "replay_value.vcd",
        "finalize_result.vcd",
        "attention_decode_score_multivalue_gqa_group_activity_manifest.json",
    ):
        path = activity_dir / name
        if path.is_file():
            path.unlink()
    activity_manifest = generate_phase_activity(
        _load(config),
        activity_dir,
        block_count=3,
        head_dim=128,
        clock_period_ns=clock_period_ns,
    )
    activity_manifest_path = (
        activity_dir / "attention_decode_score_multivalue_gqa_group_activity_manifest.json"
    )
    upper_bound_energy = _GQA_HEADS * cluster_baseline["full_context_energy_j"]
    rows: list[JsonDict] = []
    for metric in _feasible_metrics(group_metrics_csv, clock_period_ns):
        params = _params(metric)
        flow_variant = str(params["FLOW_VARIANT"])
        candidate: JsonDict = {
            "candidate_id": f"multivalue_gqa_group_activity_{flow_variant}",
            "flow_variant": flow_variant,
            "ppa_metric": _metric_provenance(metric, group_metrics_csv),
        }
        try:
            activity_power = build_power_report(
                manifest=activity_manifest,
                manifest_path=activity_manifest_path,
                design_config=group_orfs_design_config,
                flow_variant=flow_variant,
                scope="tb/dut",
                min_vcd_coverage=0.05,
                min_vcd_pins=32,
                min_macro_active_coverage=0.01,
                min_macro_active_pins=16,
                timeout_seconds=1800,
            )
            direct_energy = activity_power.get("full_context_energy_j")
            if activity_power.get("promotion_gate_pass"):
                direct_energy = _finite_positive(
                    direct_energy, "group activity power full_context_energy_j"
                )
            bound_pass = (
                direct_energy is not None
                and math.isfinite(float(direct_energy))
                and float(direct_energy) <= upper_bound_energy
            )
            candidate["activity_power"] = activity_power
            candidate["direct_group_full_context_energy_j"] = direct_energy
            candidate["independent_cluster_upper_bound"] = {
                "factor": _GQA_HEADS,
                "cluster_full_context_energy_j": cluster_baseline["full_context_energy_j"],
                "energy_j": upper_bound_energy,
                "comparison": "direct_group_full_context_energy_j <= 8 * cluster_best.activity_power.full_context_energy_j",
                "pass": bound_pass,
            }
            candidate["independent_cluster_upper_bound_energy_j"] = upper_bound_energy
            candidate["energy_upper_bound_pass"] = bound_pass
            candidate["status"] = (
                "activity_backed"
                if activity_power.get("promotion_gate_pass")
                else "rejected_gate"
            )
        except Exception as exc:  # preserve a sanitized negative row for physical-tool failures
            candidate["status"] = "measurement_failed"
            candidate["failure"] = _sanitized_failure(exc)
        rows.append(candidate)
    promoted = [row for row in rows if row["status"] == "activity_backed"]
    best = None
    if promoted:
        best = min(
            promoted,
            key=lambda row: (
                float(row["direct_group_full_context_energy_j"]),
                float(row["ppa_metric"]["instance_area_um2"]),
                float(row["ppa_metric"]["critical_path_ns"]),
            ),
        )
    return {
        "version": 1,
        "model": "decoder_attention_decode_score_multivalue_gqa_group_activity_power_v1",
        "decision": (
            "activity_backed_gqa_group_power_measured"
            if best is not None
            else "activity_power_rejected_no_gated_candidate"
        ),
        "promotion_gate_pass": best is not None,
        "candidate_count": len(rows),
        "promoted_candidate_count": len(promoted),
        "best_candidate_id": best["candidate_id"] if best is not None else None,
        "best": best,
        "candidates": rows,
        "energy_scope": "one GQA8 group full-context decode attention command",
        "independent_cluster_upper_bound_factor": _GQA_HEADS,
        "cluster_baseline": cluster_baseline,
        "cluster_baseline_full_context_energy_j": cluster_baseline["full_context_energy_j"],
        "activity_contract": {
            "scope": activity_manifest.get("scope"),
            "scope_semantics": activity_manifest.get("scope_semantics"),
            "clock_period_ns": activity_manifest["clock_period_ns"],
            "query_heads_per_kv": activity_manifest["query_heads_per_kv"],
            "representative_block_count": activity_manifest["block_count"],
            "representative_full_transaction_cycles": activity_manifest[
                "representative_full_transaction_cycles"
            ],
            "phase_partition_cycle_sum": activity_manifest["phase_partition_cycle_sum"],
            "phases": activity_manifest["phases"],
        },
        "equivalence": equivalence,
        "source_dependencies": [
            "l2_decoder_attention_decode_score_multivalue_gqa_group_equivalence_llama7b_v1",
            "l1_decoder_attention_decode_score_multivalue_gqa_group_pnr_v1",
            "prior_single_cluster_activity_power_best_activity_power",
        ],
        "remaining_abstractions": [
            "The direct result covers one GQA8 group command at the configured full context, not a total-token or full-model energy estimate.",
            "The 8x independent-cluster value is an explicit comparison upper bound, not a regenerated cluster measurement or a FLOW_VARIANT pairing.",
            "FakeRAM area and power use Nangate45 proxy LEF/Liberty views, not SRAM compiler signoff.",
            "Off-group value memory, NoC, HBM/DRAM, command distribution, and clock-tree composition are outside this result.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--group-metrics-csv", type=Path, required=True)
    parser.add_argument("--cluster-activity-power-json", type=Path, required=True)
    parser.add_argument("--equivalence-json", type=Path, required=True)
    parser.add_argument("--group-orfs-design-config", type=Path, required=True)
    parser.add_argument("--clock-period-ns", type=float, default=8.0)
    parser.add_argument("--activity-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        config=args.config,
        group_metrics_csv=args.group_metrics_csv,
        cluster_activity_power_json=args.cluster_activity_power_json,
        equivalence_json=args.equivalence_json,
        group_orfs_design_config=args.group_orfs_design_config,
        clock_period_ns=args.clock_period_ns,
        activity_dir=args.activity_dir,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

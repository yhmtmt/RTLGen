#!/usr/bin/env python3
"""Measure activity-backed power across feasible multivalue-cluster PPA rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any

from npu.eval.generate_attention_decode_score_multivalue_cluster_activity import (
    generate_phase_activity,
)
from npu.synth.run_postroute_vcd_power import build_report as build_power_report


JsonDict = dict[str, Any]
_MAX_FAILURE_DETAIL_LINES = 16
_MAX_FAILURE_DETAIL_LINE_CHARS = 400
_MAX_FAILURE_DETAIL_BYTES = 4096
_ABSOLUTE_PATH_RE = re.compile(r"/[^\s\"'`<>|&(){}\[\]]+")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVALUATOR_LOCAL_PATH_PLACEHOLDER = "<evaluator-local-path>"


def _redact_path(path: str) -> str:
    normalized = path.rstrip(".,;:!?)]}")
    token = Path(normalized)
    if token.is_absolute():
        try:
            return str(token.relative_to(_REPO_ROOT))
        except ValueError:
            return _EVALUATOR_LOCAL_PATH_PLACEHOLDER
    return normalized


def _sanitize_failure_line(line: str) -> str:
    return _ABSOLUTE_PATH_RE.sub(
        lambda match: _redact_path(match.group(0)),
        line,
    )


def _collect_failure_detail(lines: list[str]) -> list[str]:
    detail = [line.strip() for line in lines if line.strip()]
    detail = [line for line in detail if line]
    detail = [line[:_MAX_FAILURE_DETAIL_LINE_CHARS] for line in detail[-_MAX_FAILURE_DETAIL_LINES:]]
    while detail and sum(len(line) for line in detail) > _MAX_FAILURE_DETAIL_BYTES:
        detail = detail[1:]
    return detail


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
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
        "metrics_csv": str(metrics_csv),
        **{field: row[field] for field in fields if str(row.get(field, "")).strip()},
    }


def _feasible_metrics(
    metrics_csv: Path,
    clock_period_ns: float,
    *,
    required_flow_variant: str | None = None,
    required_synth_args: str | None = None,
) -> list[JsonDict]:
    normalized_required_flow_variant = str(required_flow_variant or "").strip() or None
    normalized_required_synth_args = str(required_synth_args or "").strip() or None

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
        synth_args = str(params.get("SYNTH_ARGS", "")).strip()
        if not flow_variant or abs(row_clock - clock_period_ns) > 1e-9:
            continue
        if (
            normalized_required_flow_variant is not None
            and flow_variant != normalized_required_flow_variant
        ):
            continue
        if (
            normalized_required_synth_args is not None
            and synth_args != normalized_required_synth_args
        ):
            continue
        if not math.isfinite(critical_path) or critical_path > clock_period_ns:
            continue
        previous = selected.get(flow_variant)
        if previous is None or float(row.get("instance_area_um2") or math.inf) < float(
            previous.get("instance_area_um2") or math.inf
        ):
            selected[flow_variant] = row
    if not selected:
        if normalized_required_flow_variant is not None or normalized_required_synth_args is not None:
            details = []
            if normalized_required_flow_variant is not None:
                details.append(f"FLOW_VARIANT={normalized_required_flow_variant}")
            if normalized_required_synth_args is not None:
                details.append(f"SYNTH_ARGS={normalized_required_synth_args}")
            raise ValueError(
                f"no status=ok timing-feasible rows in {metrics_csv} matching "
                f"{', '.join(details)} at {clock_period_ns:g} ns"
            )
        raise ValueError(
            f"no status=ok timing-feasible {clock_period_ns:g} ns rows in {metrics_csv}"
        )
    return sorted(
        selected.values(),
        key=lambda row: (
            float(row.get("die_area") or math.inf),
            float(row.get("instance_area_um2") or math.inf),
            float(row.get("critical_path_ns") or math.inf),
        ),
    )


def _sanitized_failure(exc: Exception) -> JsonDict:
    lines = [_sanitize_failure_line(line).strip() for line in str(exc).splitlines()]
    lines = [line for line in lines if line]
    if lines:
        summary = lines[0][:240]
    else:
        summary = f"{type(exc).__name__} failure"
    sanitized_lines = _collect_failure_detail(lines)
    if not sanitized_lines:
        sanitized_lines = lines[-_MAX_FAILURE_DETAIL_LINES:]
    return {
        "error_type": type(exc).__name__,
        "error_summary": summary,
        "detail": sanitized_lines,
    }


def _write_markdown(payload: JsonDict, path: Path) -> None:
    lines = [
        "# Shared-score multivalue cluster activity power",
        "",
        f"- decision: `{payload['decision']}`",
        f"- promoted candidates: `{payload['promoted_candidate_count']}`",
        f"- measured candidates: `{payload['candidate_count']}`",
        "",
        "| variant | path ns | instance mm2 | status | head cycles | head latency ms | energy mJ |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in payload["candidates"]:
        metric = row["ppa_metric"]
        activity = row.get("activity_power", {})
        energy = activity.get("full_context_energy_j")
        lines.append(
            "| {variant} | {path_ns} | {area_mm2:.6f} | {status} | {cycles} | {latency_ms} | {energy_mj} |".format(
                variant=row["flow_variant"],
                path_ns=metric.get("critical_path_ns"),
                area_mm2=float(metric.get("instance_area_um2", 0.0)) / 1.0e6,
                status=row["status"],
                cycles=activity.get("full_context_cycles"),
                latency_ms=(
                    float(activity["full_context_latency_s"]) * 1.0e3
                    if activity.get("full_context_latency_s") is not None
                    else None
                ),
                energy_mj=float(energy) * 1.0e3 if energy is not None else None,
            )
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    *,
    config: Path,
    cluster_metrics_csv: Path,
    equivalence_json: Path,
    orfs_design_config: Path,
    clock_period_ns: float,
    activity_dir: Path,
    min_sequential_register_activity_coverage: float = 0.95,
    required_flow_variant: str | None = None,
    required_synth_args: str | None = None,
    source_pnr_item_id: str | None = None,
) -> JsonDict:
    if not (0.0 < min_sequential_register_activity_coverage <= 1.0):
        raise ValueError("min_sequential_register_activity_coverage must be in (0, 1]")
    equivalence = _load(equivalence_json)
    if not equivalence.get("equivalence_pass"):
        raise ValueError("multivalue-cluster end-to-end equivalence did not pass")
    activity_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "score_fill.vcd",
        "replay_value.vcd",
        "finalize_result.vcd",
        "attention_decode_score_multivalue_cluster_activity_manifest.json",
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
        activity_dir / "attention_decode_score_multivalue_cluster_activity_manifest.json"
    )
    rows: list[JsonDict] = []
    for metric in _feasible_metrics(
        cluster_metrics_csv,
        clock_period_ns,
        required_flow_variant=required_flow_variant,
        required_synth_args=required_synth_args,
    ):
        params = _params(metric)
        flow_variant = str(params["FLOW_VARIANT"])
        candidate: JsonDict = {
            "candidate_id": f"multivalue_cluster_activity_{flow_variant}",
            "flow_variant": flow_variant,
            "ppa_metric": _metric_provenance(metric, cluster_metrics_csv),
        }
        try:
            activity_power = build_power_report(
                manifest=activity_manifest,
                manifest_path=activity_manifest_path,
                design_config=orfs_design_config,
                flow_variant=flow_variant,
                scope="tb/dut",
                min_vcd_coverage=0.05,
                min_vcd_pins=32,
                min_sequential_register_activity_coverage=min_sequential_register_activity_coverage,
                min_macro_active_coverage=0.01,
                min_macro_active_pins=16,
                timeout_seconds=1800,
            )
            candidate["activity_power"] = activity_power
            candidate["status"] = (
                "activity_backed" if activity_power.get("promotion_gate_pass") else "rejected_gate"
            )
        except Exception as exc:  # preserve an explicit negative row for physical-tool failures
            candidate["status"] = "measurement_failed"
            candidate["failure"] = _sanitized_failure(exc)
        rows.append(candidate)
    promoted = [row for row in rows if row["status"] == "activity_backed"]
    best = None
    if promoted:
        best = min(
            promoted,
            key=lambda row: (
                float(row["activity_power"]["full_context_energy_j"]),
                float(row["ppa_metric"]["instance_area_um2"]),
                float(row["ppa_metric"]["critical_path_ns"]),
            ),
        )
    return {
        "version": 1,
        "model": "decoder_attention_decode_score_multivalue_cluster_activity_power_v1",
        "decision": (
            "activity_backed_cluster_power_measured"
            if best is not None
            else "activity_power_rejected_no_gated_candidate"
        ),
        "promotion_gate_pass": best is not None,
        "candidate_count": len(rows),
        "promoted_candidate_count": len(promoted),
        "best_candidate_id": best["candidate_id"] if best is not None else None,
        "best": best,
        "candidates": rows,
        "activity_contract": {
            "clock_period_ns": activity_manifest["clock_period_ns"],
            "representative_block_count": activity_manifest["block_count"],
            "representative_full_transaction_cycles": activity_manifest[
                "representative_full_transaction_cycles"
            ],
            "phase_partition_cycle_sum": activity_manifest["phase_partition_cycle_sum"],
            "phases": activity_manifest["phases"],
        },
        "precision_status": "unchanged_integer_contract_from_merged_multivalue_equivalence",
        "equivalence": {
            "equivalence_pass": True,
            "decision": equivalence.get("decision"),
            "score_tensor_hash": equivalence.get("score_tensor_hash"),
            "final_tensor_hash": equivalence.get("final_tensor_hash"),
        },
        "source_dependencies": (
            [
                str(source_pnr_item_id).strip(),
                "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
            ]
            if str(source_pnr_item_id or "").strip()
            else [
                "l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2",
                "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
            ]
        ),
        "selection_contract": {
            "required_flow_variant": str(required_flow_variant or "").strip() or None,
            "required_synth_args": str(required_synth_args or "").strip() or None,
            "min_sequential_register_activity_coverage": min_sequential_register_activity_coverage,
        },
        "remaining_abstractions": [
            "FakeRAM area and power use Nangate45 proxy LEF/Liberty views, not SRAM compiler signoff.",
            "Value-memory, NoC, HBM/DRAM, command-distribution, and clock-tree composition outside the cluster are not included.",
            "RTL VCD is mapped to the routed netlist; each candidate records and gates direct annotation coverage.",
            "Score multiplier and shift derivation remain external to the cluster boundary.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--cluster-metrics-csv", type=Path, required=True)
    parser.add_argument("--equivalence-json", type=Path, required=True)
    parser.add_argument("--orfs-design-config", type=Path, required=True)
    parser.add_argument("--clock-period-ns", type=float, default=8.0)
    parser.add_argument(
        "--required-flow-variant",
        default=None,
        help="Optional exact FLOW_VARIANT to require before candidate measurement",
    )
    parser.add_argument(
        "--required-synth-args",
        default=None,
        help="Optional exact SYNTH_ARGS to require before candidate measurement",
    )
    parser.add_argument(
        "--source-pnr-item-id",
        default=None,
        help="Optional source PNR work-item ID for source_dependencies tracking",
    )
    parser.add_argument(
        "--min-sequential-register-activity-coverage",
        type=float,
        default=0.95,
    )
    parser.add_argument("--activity-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        config=args.config,
        cluster_metrics_csv=args.cluster_metrics_csv,
        equivalence_json=args.equivalence_json,
        orfs_design_config=args.orfs_design_config,
        clock_period_ns=args.clock_period_ns,
        activity_dir=args.activity_dir,
        required_flow_variant=args.required_flow_variant,
        required_synth_args=args.required_synth_args,
        source_pnr_item_id=args.source_pnr_item_id,
        min_sequential_register_activity_coverage=args.min_sequential_register_activity_coverage,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

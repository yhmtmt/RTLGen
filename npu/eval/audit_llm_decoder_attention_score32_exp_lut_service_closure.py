#!/usr/bin/env python3
"""Audit service provenance for the score32 exp-LUT Llama7B attention row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _first_dict(*values: Any) -> JsonDict:
    for value in values:
        if isinstance(value, dict):
            return dict(value)
    return {}


def _pick(row: JsonDict, keys: tuple[str, ...]) -> JsonDict:
    return {key: row.get(key) for key in keys if key in row}


def _selected_score32_row(payload: JsonDict) -> JsonDict:
    return _first_dict(
        payload.get("best_requested"),
        payload.get("best_area_fit"),
        payload.get("best_feasible"),
        payload.get("best"),
    )


def _wrapper_backed(promotion: JsonDict, row: JsonDict) -> bool:
    diagnosis = _as_dict(promotion.get("diagnosis"))
    if not bool(diagnosis.get("l1_wrapper_accepted")):
        return False
    if not bool(diagnosis.get("l1_wrapper_metrics_match")):
        return False
    if not bool(diagnosis.get("l2_candidate_supported")):
        return False
    selected_metrics = str(diagnosis.get("l2_selected_wrapper_metrics_csv") or "")
    row_metrics = str(row.get("measured_dual_stream_composed_metrics_csv") or row.get("substituted_compute_metrics_csv") or "")
    return bool(selected_metrics and row_metrics and selected_metrics == row_metrics)


def _service_components(
    *,
    row: JsonDict,
    composition: JsonDict,
    measured_sram: JsonDict,
) -> list[JsonDict]:
    closure_flags = _as_dict(composition.get("closure_flags"))
    closure_diagnosis = _as_dict(composition.get("closure_diagnosis"))
    measured_sram_best = _as_dict(measured_sram.get("best"))
    return [
        {
            "component": "compute_datapath",
            "status": "measured",
            "source": row.get("measured_dual_stream_composed_metrics_csv")
            or row.get("substituted_compute_metrics_csv"),
            "details": _pick(
                row,
                (
                    "substituted_compute_semantic_profile",
                    "substituted_compute_replica_count",
                    "replica_recost_area_fit_replica_count",
                    "replica_recost_macs_per_cycle",
                    "replica_recost_latency_us",
                    "measured_command_dispatch_control_metrics_csv",
                ),
            ),
        },
        {
            "component": "command_dispatch_control",
            "status": "measured" if row.get("measured_command_dispatch_control_metrics_csv") else "missing",
            "source": row.get("measured_command_dispatch_control_metrics_csv"),
            "details": _pick(
                row,
                (
                    "measured_command_dispatch_control_variant_name",
                    "measured_command_dispatch_control_cluster_count",
                    "measured_command_dispatch_control_area_um2",
                    "measured_command_dispatch_control_clock_ns",
                    "command_dispatch_control_clock_ok",
                ),
            ),
        },
        {
            "component": "endpoint_ready_valid",
            "status": "measured" if closure_flags.get("endpoint_ppa_width_matched") else "measured_with_width_note",
            "source": composition.get("endpoint_ready_valid_json"),
            "details": {
                "endpoint_width_ratio_vs_measured_ppa": closure_diagnosis.get(
                    "endpoint_width_ratio_vs_measured_ppa"
                ),
                "endpoint_ppa_width_matched": closure_flags.get("endpoint_ppa_width_matched"),
            },
        },
        {
            "component": "router_fifo_noc",
            "status": "measured_segmented"
            if closure_flags.get("router_ppa_width_matched") and closure_flags.get("fifo_ppa_width_matched")
            else "measured_with_lane_replication",
            "source": {
                "composition": composition.get("selected_frontier", {}).get("noc_router_metrics_csv")
                if isinstance(composition.get("selected_frontier"), dict)
                else None,
                "segmented_l1_promotion": composition.get("segmented_l1_promotion_json"),
            },
            "details": _pick(
                closure_diagnosis,
                (
                    "router_lanes_for_link",
                    "router_lanes_for_packet",
                    "fifo_lanes_for_link",
                    "router_boundary_status",
                    "fifo_boundary_status",
                ),
            ),
        },
        {
            "component": "tile_local_and_shared_sram",
            "status": "measured_capacity_estimate",
            "source": measured_sram.get("local_sram_capacity_json"),
            "details": _pick(
                measured_sram_best,
                (
                    "measured_tile_local_sram_area_um2",
                    "measured_shared_sram_capacity_mib",
                    "measured_shared_sram_used_area_um2",
                    "local_capacity_bytes_per_cluster",
                    "abstract_local_capacity_bytes_per_cluster_replaced",
                ),
            ),
        },
        {
            "component": "hbm_dram_service",
            "status": "inherited_model",
            "source": row.get("measured_hbm_service_model") or row.get("hbm_service_model"),
            "details": _pick(
                row,
                (
                    "measured_hbm_service_model",
                    "effective_hbm_bytes_per_cycle",
                    "channel_count",
                    "channel_bandwidth_bytes_per_cycle",
                    "hbm_byte_share",
                    "controller_service_cycles",
                    "tile_hbm_cycles",
                ),
            ),
        },
    ]


def build_report(args: argparse.Namespace) -> JsonDict:
    measured_command = _load_json(args.measured_command_control_json)
    wrapper_promotion = _load_json(args.wrapper_promotion_json)
    composition = _load_json(args.endpoint_router_sram_composition_json)
    measured_sram = _load_json(args.measured_sram_rebalance_json)

    row = _selected_score32_row(measured_command)
    diagnosis = _as_dict(measured_command.get("diagnosis"))
    promotion_diagnosis = _as_dict(wrapper_promotion.get("diagnosis"))
    wrapper_backed = _wrapper_backed(wrapper_promotion, row)
    command_decision = str(diagnosis.get("decision") or "")
    promotion_decision = str(promotion_diagnosis.get("decision") or wrapper_promotion.get("decision") or "")
    score32_supported = (
        command_decision == "dual_stream_feasible"
        and promotion_decision == "decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded"
        and wrapper_backed
    )
    decision = (
        "score32_exp_lut_service_closure_recorded"
        if score32_supported
        else "score32_exp_lut_service_closure_blocked"
    )
    service_components = _service_components(row=row, composition=composition, measured_sram=measured_sram)
    remaining_abstractions = [
        item["component"]
        for item in service_components
        if str(item.get("status", "")).startswith("inherited")
        or str(item.get("status", "")).endswith("_estimate")
    ]

    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_exp_lut_service_closure_audit_v1",
        "decision": decision,
        "inputs": {
            "measured_command_control_json": str(args.measured_command_control_json),
            "wrapper_promotion_json": str(args.wrapper_promotion_json),
            "endpoint_router_sram_composition_json": str(args.endpoint_router_sram_composition_json),
            "measured_sram_rebalance_json": str(args.measured_sram_rebalance_json),
        },
        "diagnosis": {
            "score32_supported": score32_supported,
            "measured_command_decision": command_decision,
            "wrapper_promotion_decision": promotion_decision,
            "wrapper_metrics_match": wrapper_backed,
            "selected_semantic_profile": row.get("substituted_compute_semantic_profile"),
            "selected_wrapper_metrics_csv": row.get("measured_dual_stream_composed_metrics_csv")
            or row.get("substituted_compute_metrics_csv"),
            "latency_us": row.get("replica_recost_latency_us") or row.get("adjusted_latency_us_if_feasible"),
            "source_latency_us": row.get("latency_us"),
            "macs_per_cycle": row.get("replica_recost_macs_per_cycle") or row.get("macs_per_cycle"),
            "dominant_tile_resource": row.get("dominant_tile_resource"),
            "remaining_abstractions": remaining_abstractions,
        },
        "service_components": service_components,
        "selected_score32_row": _pick(
            row,
            (
                "latency_us",
                "adjusted_latency_us_if_feasible",
                "replica_recost_latency_us",
                "replica_recost_macs_per_cycle",
                "replica_recost_area_fit_replica_count",
                "dominant_tile_resource",
                "substituted_compute_semantic_profile",
                "measured_dual_stream_composed_metrics_csv",
                "measured_command_dispatch_control_metrics_csv",
                "measured_sram_rebalance_model",
                "measured_hbm_service_model",
                "hbm_byte_share",
                "effective_hbm_bytes_per_cycle",
            ),
        ),
        "next_step": {
            "recommended_next_step": (
                "Use this score32 exp-LUT row as the quality-backed compute/service baseline, "
                "then close the inherited HBM/DRAM service or replace SRAM macro packing with a placed memory hierarchy."
            )
            if score32_supported
            else "Resolve wrapper promotion or measured command-control support before service closure.",
            "requires_hbm_dram_closure": True,
            "requires_new_wrapper_ppa": False,
        },
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diagnosis = payload["diagnosis"]
    lines = [
        "# Score32 exp-LUT Service Closure Audit",
        "",
        f"- decision: `{payload['decision']}`",
        f"- score32 supported: `{diagnosis['score32_supported']}`",
        f"- wrapper metrics match: `{diagnosis['wrapper_metrics_match']}`",
        f"- latency us: `{diagnosis.get('latency_us')}`",
        f"- MAC/cycle: `{diagnosis.get('macs_per_cycle')}`",
        f"- remaining abstractions: `{', '.join(diagnosis.get('remaining_abstractions') or [])}`",
        "",
        "## Components",
        "",
        "| component | status | source |",
        "|---|---|---|",
    ]
    for item in payload["service_components"]:
        source = item.get("source")
        if isinstance(source, dict):
            source = ", ".join(f"{key}={value}" for key, value in source.items() if value)
        lines.append(f"| {item['component']} | {item['status']} | {source or ''} |")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            f"- {payload['next_step']['recommended_next_step']}",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measured-command-control-json", type=Path, required=True)
    parser.add_argument("--wrapper-promotion-json", type=Path, required=True)
    parser.add_argument("--endpoint-router-sram-composition-json", type=Path, required=True)
    parser.add_argument("--measured-sram-rebalance-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "decision": payload["decision"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

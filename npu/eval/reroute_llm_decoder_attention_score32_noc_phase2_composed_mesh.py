#!/usr/bin/env python3
"""Reroute score32 Phase 2 traffic using measured composed endpoint/mesh PPA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import measure_llm_decoder_attention_score32_noc_phase2_schedule as phase2_schedule  # noqa: E402
from npu.eval.audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure import (  # noqa: E402
    _as_positive_float,
    _load_json,
    _validate_phase2_schedule,
)
from npu.eval.reroute_llm_decoder_attention_score32_noc_phase2_measured_router_clock import (  # noqa: E402
    _compact_schedule,
    _schedule_args,
)

JsonDict = dict[str, Any]

DEFAULT_BASELINE_SCHEDULE = Path(
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)
DEFAULT_COMPOSED_PROMOTION = Path(
    "control_plane/shadow_exports/l1_promotions/"
    "l1_noc_sram_packet_mesh4x4_composed_ppa_v1.json"
)
_EXPECTED_COMPOSED_ITEM_ID = "l1_noc_sram_packet_mesh4x4_composed_ppa_v1"
_EXPECTED_DESIGN_TOKEN = "noc_sram_packet_mesh4x4"


def _validate_composed_promotion(payload: JsonDict) -> JsonDict:
    if payload.get("item_id") != _EXPECTED_COMPOSED_ITEM_ID:
        raise ValueError("composed promotion item_id mismatch")
    if payload.get("task_type") != "l1_sweep":
        raise ValueError("composed promotion task_type must be l1_sweep")
    record = payload.get("evaluation_record")
    proposals = payload.get("proposals")
    if not isinstance(record, dict) or not bool(record.get("physical_metrics_present")):
        raise ValueError("composed promotion must provide physical metrics")
    if record.get("timing_feasible") is False:
        raise ValueError("composed promotion is not timing-feasible")
    if not isinstance(proposals, list):
        raise ValueError("composed promotion is missing proposals")

    candidates: list[JsonDict] = []
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        ref = proposal.get("metrics_ref")
        summary = proposal.get("metric_summary")
        if not isinstance(ref, dict) or not isinstance(summary, dict):
            continue
        identity = " ".join(
            str(ref.get(key) or "") for key in ("design", "metrics_csv", "result_path")
        )
        if _EXPECTED_DESIGN_TOKEN not in identity:
            continue
        candidates.append(
            {
                "metrics_csv": str(ref.get("metrics_csv") or ""),
                "param_hash": str(ref.get("param_hash") or ""),
                "tag": str(ref.get("tag") or ""),
                "result_path": str(ref.get("result_path") or ""),
                "critical_path_ns": _as_positive_float(
                    summary.get("critical_path_ns"), "composed critical_path_ns"
                ),
                "footprint_um2": _as_positive_float(summary.get("die_area"), "composed die_area"),
                "vectorless_power_mw": _as_positive_float(
                    summary.get("total_power_mw"), "composed total_power_mw"
                ),
            }
        )
    if not candidates:
        raise ValueError("composed promotion does not contain the expected endpoint/mesh design")
    return min(
        candidates,
        key=lambda item: (
            item["critical_path_ns"],
            item["footprint_um2"],
            item["vectorless_power_mw"],
        ),
    )


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root.resolve()
    baseline_path = repo_root / args.baseline_schedule_json
    baseline = _validate_phase2_schedule(_load_json(baseline_path), source_path=baseline_path)
    composed = _validate_composed_promotion(_load_json(repo_root / args.composed_promotion_json))

    source_clock_ns = float(baseline["source_contract"]["noc_clock_ns"])
    measured_clock_ns = float(composed["critical_path_ns"])
    effective_clock_ns = max(source_clock_ns, measured_clock_ns)
    schedule = _compact_schedule(
        phase2_schedule.build_report(_schedule_args(args, noc_clock_ns=effective_clock_ns))
    )
    if schedule["scheduled_flit_count"] != schedule["delivered_flit_count"]:
        raise ValueError("composed-clock reroute did not deliver every scheduled flit")

    drain_time_ns = float(schedule["drain_time_ns"])
    vectorless_energy_mj = composed["vectorless_power_mw"] * drain_time_ns / 1.0e9
    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_composed_mesh_reroute",
        "decision": "score32_noc_phase2_composed_mesh_reroute_recorded",
        "diagnosis": {
            "decision": "score32_noc_phase2_composed_mesh_reroute_recorded",
            "workload_complete": True,
            "within_compute_envelope": bool(schedule["drain_within_source_compute_layer_envelope"]),
            "remaining_onchip_communication_abstraction": "sram_macro_placement_and_activity_only",
        },
        "source_items": {
            "baseline_schedule": baseline["item_id"],
            "composed_endpoint_mesh": _EXPECTED_COMPOSED_ITEM_ID,
        },
        "clock_contract": {
            "source_schedule_noc_clock_ns": source_clock_ns,
            "measured_composed_logic_critical_path_ns": measured_clock_ns,
            "effective_noc_clock_ns": effective_clock_ns,
            "source_clock_floor_reason": (
                "The composed wrapper excludes SRAM bitcell/macro timing and workload-matched service; "
                "a faster logic result alone does not justify reducing the existing 1ns schedule floor."
            ),
            "release_conversion_and_mesh_routing_rerun": True,
            "absolute_source_cycle_timeline_reused": False,
        },
        "schedule": schedule,
        "physical_accounting": {
            **composed,
            "scope": "placed_16_endpoint_16_router_control_fabric_with_bounded_harness",
            "footprint_status": "floorplan_envelope_includes_harness_not_cell_area",
            "power_status": "vectorless_not_workload_matched",
            "vectorless_drain_energy_mj": vectorless_energy_mj,
            "energy_status": "diagnostic_vectorless_power_times_rerouted_drain_time",
        },
        "closure_flags": {
            "all_16_endpoints_and_routers_physically_anchored_together": True,
            "fresh_full_workload_reroute": True,
            "aggregate_wiring_and_congestion_included": True,
            "sram_bitcells_included": False,
            "workload_matched_switching_power": False,
            "hbm_dram_included": False,
        },
        "remaining_abstractions": [
            "SRAM bitcells/macros, macro placement, and macro access energy are outside the composed RTL wrapper.",
            "The OpenROAD power estimate is vectorless rather than driven by the measured Phase 2 toggle trace.",
            "HBM/DRAM timing, controller implementation, and vendor current signoff remain external envelopes.",
            "Producer, reducer arithmetic, and root-finalizer compute are measured by separate compatible "
            "anchors, not this NoC wrapper.",
        ],
    }


def write_report(payload: JsonDict, path: Path) -> None:
    schedule = payload["schedule"]
    physical = payload["physical_accounting"]
    lines = [
        "# Llama7B Score32 Composed Endpoint/Mesh Reroute",
        "",
        "- measured composed critical path ns: "
        f"`{payload['clock_contract']['measured_composed_logic_critical_path_ns']}`",
        f"- effective NoC clock ns: `{payload['clock_contract']['effective_noc_clock_ns']}`",
        f"- drain time ns: `{schedule['drain_time_ns']}`",
        f"- within compute envelope: `{str(schedule['drain_within_source_compute_layer_envelope']).lower()}`",
        f"- composed footprint um2: `{physical['footprint_um2']}`",
        f"- vectorless power mW: `{physical['vectorless_power_mw']}`",
        f"- diagnostic vectorless drain energy mJ: `{physical['vectorless_drain_energy_mj']}`",
        "",
        "## Remaining Abstractions",
        "",
        *(f"- {item}" for item in payload["remaining_abstractions"]),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--source-json", type=Path, default=phase2_schedule.DEFAULT_SOURCE_JSON)
    parser.add_argument("--measured-l1-costs", type=Path, default=phase2_schedule.DEFAULT_MEASURED_L1_COSTS)
    parser.add_argument("--baseline-schedule-json", type=Path, default=DEFAULT_BASELINE_SCHEDULE)
    parser.add_argument("--composed-promotion-json", type=Path, default=DEFAULT_COMPOSED_PROMOTION)
    parser.add_argument("--max-cycles", type=int, default=1000000)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

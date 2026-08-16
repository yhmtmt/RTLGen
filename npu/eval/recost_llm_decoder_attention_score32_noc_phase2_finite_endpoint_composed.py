#!/usr/bin/env python3
"""Recost the Llama7B score32 point with finite endpoints and composed NoC PPA."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import measure_llm_decoder_attention_score32_noc_phase2_schedule as phase2_schedule  # noqa: E402
from npu.eval.audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure import (  # noqa: E402
    _load_json,
    _validate_phase2_schedule,
)
from npu.eval.reroute_llm_decoder_attention_score32_noc_phase2_composed_mesh import (  # noqa: E402
    _validate_composed_promotion,
)
from npu.eval.reroute_llm_decoder_attention_score32_noc_phase2_measured_router_clock import (  # noqa: E402
    _compact_schedule,
    _schedule_args,
)
from npu.eval.verify_llm_decoder_attention_score32_noc_phase2_endpoint_rtl import (  # noqa: E402
    descriptors_from_packet_specs,
    run_performance_replay,
)
from npu.eval.measure_llm_decoder_attention_score32_noc_phase2_schedule import (  # noqa: E402
    PacketSpec,
)

JsonDict = dict[str, Any]

_BASE = Path("runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1")
DEFAULT_BASELINE_SCHEDULE = _BASE / (
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)
DEFAULT_ENDPOINT_EQUIVALENCE = _BASE / (
    "decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence__"
    "l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1.json"
)
DEFAULT_COMPOSED_PROMOTION = Path(
    "control_plane/shadow_exports/l1_promotions/"
    "l1_noc_sram_packet_mesh4x4_composed_ppa_v1.json"
)

_EXPECTED_ENDPOINT_PROFILE = "decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence"
_COUNTER_FIELDS = ("packets", "flits", "cycles", "contention", "input_stalls", "max_occupancy")


def _positive_number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def _positive_int(value: Any, label: str) -> int:
    number = _positive_number(value, label)
    integer = int(number)
    if float(integer) != number:
        raise ValueError(f"{label} must be an integer")
    return integer


def _validate_endpoint_equivalence(payload: JsonDict, *, baseline: JsonDict) -> JsonDict:
    if payload.get("version") != 1 or payload.get("profile") != _EXPECTED_ENDPOINT_PROFILE:
        raise ValueError("endpoint equivalence profile/version mismatch")
    if payload.get("coverage") != "workload_complete":
        raise ValueError("endpoint equivalence must be workload_complete")
    source = payload.get("source_schedule")
    rtl = payload.get("rtl_replay")
    performance = payload.get("endpoint_aware_performance_replay")
    equivalence = payload.get("equivalence")
    if not all(isinstance(section, dict) for section in (source, rtl, performance, equivalence)):
        raise ValueError("endpoint equivalence is missing required sections")
    required_flags = (
        "all_packets_completed",
        "all_flits_written",
        "rx_descriptor_precedes_tx_enforced",
        "cycle_and_router_counter_match",
    )
    if not all(equivalence.get(flag) is True for flag in required_flags):
        raise ValueError("endpoint equivalence does not pass every required flag")
    if equivalence.get("wire_tag_width_bits") != 8:
        raise ValueError("endpoint equivalence must use concrete 8-bit tags")
    mismatches = {
        field: {"rtl": rtl.get(field), "performance": performance.get(field)}
        for field in _COUNTER_FIELDS
        if rtl.get(field) != performance.get(field)
    }
    if mismatches:
        raise ValueError(f"endpoint RTL/performance counters differ: {mismatches}")
    baseline_simulation = dict(baseline.get("simulation") or {})
    expected_source = {
        "packet_count": baseline_simulation.get("scheduled_packet_count"),
        "flit_count": baseline_simulation.get("scheduled_flit_count"),
        "logical_release_queue_cycles_to_drain": baseline_simulation.get("cycles_to_drain"),
    }
    source_mismatches = {
        key: {"expected": expected, "observed": source.get(key)}
        for key, expected in expected_source.items()
        if source.get(key) != expected
    }
    if source_mismatches:
        raise ValueError(f"endpoint equivalence source schedule mismatch: {source_mismatches}")
    return {field: int(rtl[field]) for field in _COUNTER_FIELDS}


def _prior_component_totals(best: JsonDict) -> JsonDict:
    area_um2 = 0.0
    power_mw = 0.0
    details: list[JsonDict] = []
    for name in ("noc_router", "noc_fifo", "onchip_endpoint"):
        count = _positive_number(best.get(f"{name}_per_cluster"), f"{name}_per_cluster") * _positive_number(
            best.get("cluster_count"), "cluster_count"
        )
        area_each = _positive_number(best.get(f"{name}_area_um2"), f"{name}_area_um2")
        power_each = _positive_number(best.get(f"{name}_power_mw"), f"{name}_power_mw")
        area_um2 += count * area_each
        power_mw += count * power_each
        details.append(
            {
                "component": name,
                "count": int(count),
                "area_um2_each": area_each,
                "power_mw_each": power_each,
            }
        )
    return {"area_um2": area_um2, "power_mw": power_mw, "components": details}


def _build_physical_recost(*, source_recost: JsonDict, composed: JsonDict, token_time_ns: float) -> JsonDict:
    best = dict(source_recost.get("best_requested") or {})
    if not best:
        raise ValueError("source recost is missing best_requested")
    prior = _prior_component_totals(best)
    source_logic_area_um2 = _positive_number(best.get("logic_area_used_um2"), "logic_area_used_um2")
    source_logic_power_mw = _positive_number(
        best.get("replica_recost_compute_power_mw", best.get("logic_power_mw")),
        "source logic power",
    ) + _positive_number(best.get("measured_l1_overhead_power_mw"), "measured_l1_overhead_power_mw")
    composed_area_um2 = _positive_number(composed.get("footprint_um2"), "composed footprint")
    composed_power_mw = _positive_number(composed.get("vectorless_power_mw"), "composed power")
    recost_logic_area_um2 = source_logic_area_um2 - prior["area_um2"] + composed_area_um2
    recost_logic_power_mw = source_logic_power_mw - prior["power_mw"] + composed_power_mw
    die_area_um2 = _positive_number(best.get("die_area_mm2"), "die_area_mm2") * 1.0e6
    shared_sram_area_um2 = _positive_number(
        best.get("measured_shared_sram_used_area_um2"), "measured_shared_sram_used_area_um2"
    )
    tile_local_sram_area_um2 = _positive_number(
        best.get("measured_tile_local_sram_area_um2"), "measured_tile_local_sram_area_um2"
    )
    reserved_area_um2 = _positive_number(best.get("reserved_area_fraction"), "reserved_area_fraction") * die_area_um2
    total_embodied_area_um2 = (
        recost_logic_area_um2 + shared_sram_area_um2 + tile_local_sram_area_um2 + reserved_area_um2
    )
    return {
        "source_replaced_components": prior,
        "composed_endpoint_mesh": composed,
        "source_logic_area_um2": source_logic_area_um2,
        "recost_logic_area_um2": recost_logic_area_um2,
        "shared_sram_area_um2": shared_sram_area_um2,
        "tile_local_sram_area_um2": tile_local_sram_area_um2,
        "reserved_area_um2": reserved_area_um2,
        "total_embodied_area_um2": total_embodied_area_um2,
        "die_area_um2": die_area_um2,
        "area_fit": total_embodied_area_um2 <= die_area_um2,
        "source_logic_power_mw": source_logic_power_mw,
        "recost_logic_vectorless_power_mw": recost_logic_power_mw,
        "recost_logic_vectorless_energy_per_token_mj": recost_logic_power_mw * token_time_ns / 1.0e9,
        "power_status": "vectorless_logic_only",
        "energy_exclusions": [
            "SRAM dynamic access energy requires workload-to-macro port mapping.",
            "HBM/DRAM and controller energy remain outside the on-chip recost.",
        ],
    }


def build_report(args: argparse.Namespace) -> JsonDict:
    repo_root = args.repo_root.resolve()
    baseline_path = repo_root / args.baseline_schedule_json
    baseline = _validate_phase2_schedule(_load_json(baseline_path), source_path=baseline_path)
    endpoint_reference = _validate_endpoint_equivalence(
        _load_json(repo_root / args.endpoint_equivalence_json), baseline=baseline
    )
    composed = _validate_composed_promotion(_load_json(repo_root / args.composed_promotion_json))
    source_recost = _load_json(repo_root / args.source_json)

    source_clock_ns = _positive_number(baseline["source_contract"]["noc_clock_ns"], "source NoC clock")
    measured_clock_ns = _positive_number(composed["critical_path_ns"], "composed critical path")
    effective_clock_ns = max(source_clock_ns, measured_clock_ns)
    packet_specs: list[PacketSpec] = []
    logical_payload = phase2_schedule.build_report(
        _schedule_args(args, noc_clock_ns=effective_clock_ns), packet_spec_output=packet_specs
    )
    logical_schedule = _compact_schedule(logical_payload)
    finite = run_performance_replay(
        descriptors_from_packet_specs(packet_specs), max_cycles=args.max_cycles
    )
    if finite["packets"] != logical_schedule["scheduled_packet_count"]:
        raise ValueError("finite endpoint replay packet count differs from rerouted schedule")
    if finite["flits"] != logical_schedule["scheduled_flit_count"]:
        raise ValueError("finite endpoint replay flit count differs from rerouted schedule")
    if effective_clock_ns == source_clock_ns:
        mismatch = {
            field: {"merged_equivalence": endpoint_reference[field], "recost": finite[field]}
            for field in _COUNTER_FIELDS
            if endpoint_reference[field] != finite[field]
        }
        if mismatch:
            raise ValueError(f"finite endpoint recost drifted from merged equivalence: {mismatch}")

    compute_layer_time_ns = _positive_number(
        logical_schedule["compute_layer_time_ns"], "compute layer time"
    )
    finite_drain_time_ns = finite["cycles"] * effective_clock_ns
    critical_layer_time_ns = max(compute_layer_time_ns, finite_drain_time_ns)
    source_contract = dict(source_recost.get("corrected_contract") or {})
    layers = int(_positive_number(source_contract.get("layers"), "layers"))
    token_time_ns = critical_layer_time_ns * layers
    token_throughput_per_s = 1.0e9 / token_time_ns
    source_throughput = _positive_number(
        source_contract.get("token_throughput_per_s"), "source token throughput"
    )
    physical = _build_physical_recost(
        source_recost=source_recost,
        composed=composed,
        token_time_ns=token_time_ns,
    )
    best = dict(source_recost.get("best_requested") or {})
    attention_heads = _positive_int(best.get("attention_heads"), "attention_heads")
    kv_heads = _positive_int(best.get("kv_heads"), "kv_heads")
    if attention_heads % kv_heads != 0:
        raise ValueError("attention_heads must be divisible by kv_heads")
    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost",
        "decision": "score32_noc_phase2_finite_endpoint_composed_recost_recorded",
        "source_items": {
            "baseline_schedule": "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1",
            "endpoint_equivalence": (
                "l2_decoder_attention_score32_noc_phase2_endpoint_rtl_equivalence_llama7b_v1"
            ),
            "composed_endpoint_mesh": "l1_noc_sram_packet_mesh4x4_composed_ppa_v1",
        },
        "clock_contract": {
            "source_schedule_noc_clock_ns": source_clock_ns,
            "measured_composed_logic_critical_path_ns": measured_clock_ns,
            "effective_noc_clock_ns": effective_clock_ns,
            "source_clock_floor_preserved": measured_clock_ns < source_clock_ns,
            "release_conversion_rerun": True,
            "finite_endpoint_replay_rerun": True,
        },
        "logical_schedule": logical_schedule,
        "finite_endpoint_schedule": {
            **finite,
            "drain_time_ns": finite_drain_time_ns,
            "cadence_delta_cycles_vs_logical": finite["cycles"] - logical_schedule["cycles_to_drain"],
            "cadence_delta_ns_vs_logical": finite_drain_time_ns - logical_schedule["drain_time_ns"],
        },
        "throughput": {
            "layers": layers,
            "compute_layer_time_ns": compute_layer_time_ns,
            "finite_endpoint_drain_time_ns": finite_drain_time_ns,
            "critical_layer_time_ns": critical_layer_time_ns,
            "bottleneck": "finite_endpoint_noc" if finite_drain_time_ns > compute_layer_time_ns else "compute",
            "token_latency_us": token_time_ns / 1000.0,
            "token_throughput_per_s": token_throughput_per_s,
            "source_token_throughput_per_s": source_throughput,
            "throughput_ratio_vs_source": token_throughput_per_s / source_throughput,
        },
        "physical_recost": physical,
        "model_contract": {
            "contract_scope": "llama7b_shaped_gqa8_proxy_not_exact_llama2_7b",
            "hidden_size": _positive_int(best.get("hidden_size"), "hidden_size"),
            "layers": layers,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "gqa_group_size": attention_heads // kv_heads,
            "kv_sharing": best.get("kv_sharing"),
            "sequence_length": _positive_int(best.get("sequence_length"), "sequence_length"),
        },
        "precision_contract": {
            "precision_profile": best.get("precision_profile"),
            "semantic_profile": best.get("measured_dual_stream_composed_semantic_profile"),
            "arithmetic_changed_by_this_recost": False,
            "quality_evidence_inherited": True,
        },
        "closure_flags": {
            "finite_endpoint_and_mesh_cycle_equivalence_consumed": True,
            "aggregate_endpoint_mesh_ppa_consumed": True,
            "prior_primitive_area_power_replaced_not_added": True,
            "sram_bitcells_physically_composed": False,
            "command_scheduler_ppa_measured": False,
            "workload_matched_power": False,
            "hbm_dram_controller_included": False,
        },
        "remaining_abstractions": [
            "The deterministic workload command scheduler is functional testbench logic, not synthesized PPA.",
            "SRAM arrays use transaction-accurate ports; macro placement, port timing, and access energy are not composed.",
            "The composed OpenROAD power is vectorless rather than workload-activity driven.",
            "HBM/DRAM controller implementation and off-chip energy remain outside the design boundary.",
        ],
    }


def write_report(payload: JsonDict, path: Path) -> None:
    finite = payload["finite_endpoint_schedule"]
    throughput = payload["throughput"]
    physical = payload["physical_recost"]
    precision = payload["precision_contract"]
    lines = [
        "# Llama7B Finite-Endpoint Composed NoC Recost",
        "",
        f"- effective NoC clock ns: `{payload['clock_contract']['effective_noc_clock_ns']}`",
        f"- finite drain cycles/time ns: `{finite['cycles']}` / `{finite['drain_time_ns']}`",
        f"- endpoint cadence delta cycles: `{finite['cadence_delta_cycles_vs_logical']}`",
        f"- bottleneck: `{throughput['bottleneck']}`",
        f"- token throughput/s: `{throughput['token_throughput_per_s']}`",
        f"- total embodied area um2: `{physical['total_embodied_area_um2']}`",
        f"- area fit: `{str(physical['area_fit']).lower()}`",
        f"- recost logic vectorless energy/token mJ: `{physical['recost_logic_vectorless_energy_per_token_mj']}`",
        f"- precision profile: `{precision['precision_profile']}`",
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
    parser.add_argument("--endpoint-equivalence-json", type=Path, default=DEFAULT_ENDPOINT_EQUIVALENCE)
    parser.add_argument("--composed-promotion-json", type=Path, default=DEFAULT_COMPOSED_PROMOTION)
    parser.add_argument("--max-cycles", type=int, default=2000000)
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

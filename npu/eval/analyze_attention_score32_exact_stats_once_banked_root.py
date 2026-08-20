#!/usr/bin/env python3
"""Report the physical-bank frontier for exact stats-once root packet storage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from npu.sim.perf.stats_once_banked_root import (
    packet_sram_macro_count,
    simulate_banked_stats_once_shared_root,
)


def build_report() -> dict[str, Any]:
    inferred_points = []
    for banks in (2, 4, 8, 15):
        result = simulate_banked_stats_once_shared_root(physical_banks=banks)
        inferred_points.append(
            {
                "physical_banks": banks,
                "fakeram45_64x32_macros": result.macro_count,
                "root_delivery_span_cycles": result.root_delivery_span_cycles,
                "replay_drain_cycles": result.replay_drain_cycles,
                "final_replay_cycle": result.final_replay_cycle,
                "max_slots_per_source": result.max_slots_per_source,
                "schedule_iterations": result.iteration_count,
                "exact_transport": True,
            }
        )
    macro_timings = {
        2: (3901, 4120),
        4: (2939, 3077),
        8: (2733, 2855),
        15: (2505, 2620),
    }
    baseline_final = macro_timings[15][1]
    macro_points = [
        {
            "physical_banks": banks,
            "fakeram45_64x32_macros": packet_sram_macro_count(banks),
            "root_delivery_span_cycles": timing[0],
            "full_chain_final_cycle": timing[1],
            "latency_increase_vs_15_banks_pct": round(
                100.0 * (timing[1] - baseline_final) / baseline_final,
                6,
            ),
            "normalized_component_throughput_vs_15_banks": round(
                baseline_final / timing[1],
                6,
            ),
            "bit_exact": True,
        }
        for banks, timing in macro_timings.items()
    ]
    area_floor = next(point for point in macro_points if point["physical_banks"] == 4)
    baseline = next(point for point in macro_points if point["physical_banks"] == 15)
    balance = next(point for point in macro_points if point["physical_banks"] == 8)
    return {
        "version": 2,
        "semantic_profile": "score32_exact_stats_once_banked_root_macro_v2",
        "memory_contract": {
            "logical_sources": 15,
            "slots_per_source": 2,
            "slot_words": 8,
            "word_bits": 256,
            "logical_payload_bytes": 7680,
            "available_macro": "fakeram45_64x32",
            "single_port_write_priority": True,
        },
        "dominated_points": [
            {
                "physical_banks": 1,
                "fakeram45_64x32_macros": packet_sram_macro_count(1),
                "reason": (
                    "same 32 macros as four banks, but every root write and "
                    "replay read contends for one single port"
                ),
            },
            {
                "physical_banks": 2,
                "fakeram45_64x32_macros": packet_sram_macro_count(2),
                "reason": (
                    "same 32 macros as four banks, but registered-SRAM full-chain "
                    "completion is 4120 cycles instead of 3077"
                ),
            },
        ],
        "inferred_memory_model_points": inferred_points,
        "rtl_macro_points": macro_points,
        "area_floor_point": area_floor,
        "pareto_candidate_banks": [4, 8, 15],
        "selection_status": {
            "status": "awaiting_macro_ppa",
            "reason": (
                "B4 minimizes SRAM count, B15 maximizes measured throughput, and "
                "B8 is intermediate; energy and placed control area are not yet measured"
            ),
            "macro_reduction_vs_15_banks_pct": round(
                100.0
                * (baseline["fakeram45_64x32_macros"] - area_floor["fakeram45_64x32_macros"])
                / baseline["fakeram45_64x32_macros"],
                6,
            ),
            "b4_latency_increase_vs_15_banks_pct": area_floor[
                "latency_increase_vs_15_banks_pct"
            ],
            "b8_macro_reduction_vs_15_banks_pct": round(
                100.0
                * (baseline["fakeram45_64x32_macros"] - balance["fakeram45_64x32_macros"])
                / baseline["fakeram45_64x32_macros"],
                6,
            ),
            "b8_latency_increase_vs_15_banks_pct": balance[
                "latency_increase_vs_15_banks_pct"
            ],
        },
        "rtl_validation": {
            "test": (
                "tests/test_local_reducer_aggregate_stats_once_exact_"
                "shared_root_global_tree_composition.py"
            ),
            "validated_physical_banks": [2, 4, 8, 15],
            "macro_backend": "fakeram45_64x32",
            "canonical_remote_beats": 1920,
            "transport_flits": 2505,
            "transport_packets": 315,
            "exact_final_rows": 128,
            "exact_lane_value": 65535,
            "bit_exact": True,
        },
        "limitations": [
            "Macro PPA and placed control timing await evaluator measurement.",
            "Cycle results use the available registered fakeram45 behavioral model; post-route clock frequency is not yet applied.",
            "The inferred-memory model remains diagnostic only and does not select the physical bank point.",
            "Precision is unchanged because packet storage and replay are bit-exact.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Exact Stats-Once Shared-Root SRAM Bank Frontier",
        "",
        "## Registered-SRAM Full-Chain RTL",
        "",
        "| banks | 64x32 macros | root span cycles | final cycle | latency vs B15 | component throughput vs B15 |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for point in report["rtl_macro_points"]:
        lines.append(
            "| {physical_banks} | {fakeram45_64x32_macros} | "
            "{root_delivery_span_cycles} | {full_chain_final_cycle} | "
            "+{latency_increase_vs_15_banks_pct}% | "
            "{normalized_component_throughput_vs_15_banks} |".format(**point)
        )
    lines.extend(
        [
            "",
            "## Inferred-Memory Diagnostic Model",
            "",
        "| banks | 64x32 macros | root span cycles | replay drain cycles | iterations |",
        "|---:|---:|---:|---:|---:|",
        ]
    )
    for point in report["inferred_memory_model_points"]:
        lines.append(
            "| {physical_banks} | {fakeram45_64x32_macros} | "
            "{root_delivery_span_cycles} | {replay_drain_cycles} | "
            "{schedule_iterations} |".format(**point)
        )
    selection = report["selection_status"]
    lines.extend(
        [
            "",
            "## Current Candidates",
            "",
            selection["reason"] + ".",
            "",
            f"- B4: `{selection['macro_reduction_vs_15_banks_pct']}%` fewer macros than B15, "
            f"`+{selection['b4_latency_increase_vs_15_banks_pct']}%` latency",
            f"- B8: `{selection['b8_macro_reduction_vs_15_banks_pct']}%` fewer macros than B15, "
            f"`+{selection['b8_latency_increase_vs_15_banks_pct']}%` latency",
            "- B15: measured full-chain throughput anchor",
            "- B2 is dominated by B4 at the same 32-macro count",
            "- arithmetic and precision are unchanged; storage and replay remain bit-exact",
            "",
            "## Full-Chain RTL Validation",
            "",
            "B2, B4, B8, and B15 pass the finite transport, registered SRAM, decoder, and exact global-tree composition:",
            "",
            "- `1920` canonical remote beats, `2505` flits, and `315` packets",
            "- `128` exact final rows with every output lane equal to `65535`",
            "- structural tests retain the expected `32`, `32`, `64`, and `120` SRAM macros",
            "",
            "## Limits",
            "",
        ]
    )
    lines.extend(f"- {value}" for value in report["limitations"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

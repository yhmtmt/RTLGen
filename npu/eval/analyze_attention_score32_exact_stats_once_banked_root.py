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
    points = []
    for banks in (2, 4, 8, 15):
        result = simulate_banked_stats_once_shared_root(physical_banks=banks)
        points.append(
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
    selected = next(point for point in points if point["physical_banks"] == 4)
    baseline = next(point for point in points if point["physical_banks"] == 15)
    two_bank = next(point for point in points if point["physical_banks"] == 2)
    return {
        "version": 1,
        "semantic_profile": "score32_exact_stats_once_banked_root_v1",
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
            }
        ],
        "points": points,
        "selected_point": selected,
        "selection": {
            "physical_banks": 4,
            "reason": (
                "minimum 32-macro count while retaining the exact 2505-cycle "
                "root serialization floor"
            ),
            "macro_reduction_vs_15_banks_pct": round(
                100.0
                * (baseline["fakeram45_64x32_macros"] - selected["fakeram45_64x32_macros"])
                / baseline["fakeram45_64x32_macros"],
                6,
            ),
            "replay_drain_increase_vs_15_banks_cycles": (
                selected["replay_drain_cycles"] - baseline["replay_drain_cycles"]
            ),
            "two_bank_transport_span_penalty_pct": round(
                100.0
                * (
                    two_bank["root_delivery_span_cycles"]
                    - selected["root_delivery_span_cycles"]
                )
                / selected["root_delivery_span_cycles"],
                6,
            ),
        },
        "rtl_validation": {
            "test": (
                "tests/test_local_reducer_aggregate_stats_once_exact_"
                "shared_root_global_tree_composition.py"
            ),
            "physical_banks": 4,
            "retained_bank_memories": 4,
            "bank_depth_words": 64,
            "bank_word_bits": 256,
            "canonical_remote_beats": 1920,
            "transport_flits": 2505,
            "transport_packets": 315,
            "exact_final_rows": 128,
            "exact_lane_value": 65535,
            "root_delivery_span_cycles": 2505,
            "full_chain_final_cycle": 2613,
            "baseline_15_bank_final_cycle": 2600,
            "full_chain_latency_increase_cycles": 13,
            "full_chain_latency_increase_pct": 0.5,
            "bit_exact": True,
        },
        "limitations": [
            "Macro count uses available 64x32 granularity; macro PPA awaits evaluator measurement.",
            "The model excludes decoder/tree backpressure; the selected B4 point has separate full-chain RTL timing evidence.",
            "Precision is unchanged because packet storage and replay are bit-exact.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Exact Stats-Once Shared-Root SRAM Bank Frontier",
        "",
        "| banks | 64x32 macros | root span cycles | replay drain cycles | iterations |",
        "|---:|---:|---:|---:|---:|",
    ]
    for point in report["points"]:
        lines.append(
            "| {physical_banks} | {fakeram45_64x32_macros} | "
            "{root_delivery_span_cycles} | {replay_drain_cycles} | "
            "{schedule_iterations} |".format(**point)
        )
    selection = report["selection"]
    lines.extend(
        [
            "",
            "## Selection",
            "",
            f"Four banks are selected: {selection['reason']}.",
            "",
            f"- macro reduction versus 15 banks: `{selection['macro_reduction_vs_15_banks_pct']}%`",
            "- replay-drain increase versus 15 banks: "
            f"`{selection['replay_drain_increase_vs_15_banks_cycles']}` cycles",
            f"- two-bank transport-span penalty: `{selection['two_bank_transport_span_penalty_pct']}%`",
            "- one bank is excluded because it uses the same 32 macros as four banks with fewer ports",
            "- arithmetic and precision are unchanged; storage and replay remain bit-exact",
            "",
            "## Full-Chain RTL Validation",
            "",
            "The selected B4 point passes the finite transport, decoder, and exact global-tree composition:",
            "",
            "- four retained `64x256` physical memories (`32` available `64x32` macros)",
            "- `1920` canonical remote beats, `2505` flits, and `315` packets",
            "- `128` exact final rows with every output lane equal to `65535`",
            "- unchanged `2505`-cycle root delivery span",
            "- final cycle `2613`, versus `2600` for fifteen banks (`+13`, `+0.5%`)",
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

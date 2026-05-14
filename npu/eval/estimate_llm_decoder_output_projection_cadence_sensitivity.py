#!/usr/bin/env python3
"""Estimate output-projection producer cadence sensitivity to weight residency."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _int_list(value: str) -> list[int]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated integer list")
    parsed = [int(item) for item in items]
    if any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("all list items must be positive")
    return parsed


def _float_list(value: str) -> list[float]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated float list")
    parsed = [float(item) for item in items]
    if any(item < 0.0 or item > 1.0 for item in parsed):
        raise argparse.ArgumentTypeError("cache hit rates must be in [0, 1]")
    return parsed


def _load_json(path: str | Path) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def _replay_thresholds(producer_replay: JsonDict) -> dict[str, JsonDict]:
    thresholds: dict[str, JsonDict] = {}
    for row in producer_replay.get("replay_rows", []):
        if not isinstance(row, dict):
            continue
        sim = row.get("rtl_sim") if isinstance(row.get("rtl_sim"), dict) else {}
        observed = sim.get("observed") if isinstance(sim.get("observed"), dict) else {}
        if sim.get("status") != "ok" or int(observed.get("tb_backpressure", -1)) != 0:
            continue
        ranker = f"serial_lpc{int(row.get('lanes_per_cycle'))}"
        current = thresholds.get(ranker)
        producer_ii = int(row.get("producer_ii_cycles"))
        if current is None or producer_ii < int(current["min_zero_backpressure_ii_cycles"]):
            thresholds[ranker] = {
                "ranker": ranker,
                "lanes_per_cycle": int(row.get("lanes_per_cycle")),
                "ranker_service_cycles": int(row.get("ranker_service_cycles")),
                "min_zero_backpressure_ii_cycles": producer_ii,
                "observed_final_cycle": observed.get("final_cycle"),
            }
    return thresholds


def _ranker_costs(serial_ranker: JsonDict) -> dict[str, JsonDict]:
    costs: dict[str, JsonDict] = {}
    for variant in serial_ranker.get("variants", []):
        if not isinstance(variant, dict) or variant.get("status") != "ok":
            continue
        metrics = variant.get("metrics_row") if isinstance(variant.get("metrics_row"), dict) else {}
        ranker = f"serial_lpc{int(variant.get('lanes_per_cycle'))}"
        costs[ranker] = {
            "ranker": ranker,
            "lanes_per_cycle": int(variant.get("lanes_per_cycle")),
            "ranker_service_cycles": int(variant.get("ii_goal_cycles", variant.get("tile_scan_cycles", 0) + 1)),
            "critical_path_ns": _maybe_float(metrics.get("critical_path_ns")),
            "total_power_mw": _maybe_float(metrics.get("total_power_mw")),
            "die_area_um2": _maybe_float(metrics.get("die_area")),
        }
    return costs


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _choose_ranker(*, producer_ii_cycles: int, thresholds: dict[str, JsonDict], costs: dict[str, JsonDict]) -> JsonDict:
    feasible: list[JsonDict] = []
    for ranker, threshold in thresholds.items():
        if producer_ii_cycles < int(threshold["min_zero_backpressure_ii_cycles"]):
            continue
        cost = costs.get(ranker, {})
        feasible.append({**threshold, **cost})
    if not feasible:
        return {
            "ranker": None,
            "decision": "serial_ranker_not_safe_at_this_cadence",
            "reason": "No measured serial replay row has zero backpressure at or below this producer II.",
        }
    selected = min(
        feasible,
        key=lambda row: (
            row.get("total_power_mw") is None,
            row.get("total_power_mw") if row.get("total_power_mw") is not None else math.inf,
            row["lanes_per_cycle"],
        ),
    )
    return {
        **selected,
        "decision": "serial_ranker_safe",
        "reason": "Selected lowest-power serial ranker with replay-observed zero backpressure at this cadence.",
    }


def _cadence_row(
    *,
    vocab_size: int,
    hidden_size: int,
    producer_lanes: int,
    macs_per_cycle: int,
    memory_bandwidth_bytes_per_cycle: float,
    weight_cache_hit_rate: float,
    weight_bits: int,
    activation_bits: int,
    clock_ns: float,
    thresholds: dict[str, JsonDict],
    costs: dict[str, JsonDict],
) -> JsonDict:
    weight_b = _byte_width(weight_bits)
    act_b = _byte_width(activation_bits)
    tile_count = _ceil_div(vocab_size, producer_lanes)
    macs_per_tile = producer_lanes * hidden_size
    weight_bytes_per_tile = producer_lanes * hidden_size * weight_b
    charged_weight_bytes_per_tile = math.ceil(weight_bytes_per_tile * (1.0 - weight_cache_hit_rate))
    hidden_bytes_per_token = hidden_size * act_b
    compute_cycles_per_tile = _ceil_div(macs_per_tile, macs_per_cycle)
    weight_cycles_per_tile = math.ceil(charged_weight_bytes_per_tile / memory_bandwidth_bytes_per_cycle)
    hidden_load_cycles = math.ceil(hidden_bytes_per_token / memory_bandwidth_bytes_per_cycle)
    producer_ii_cycles = max(1, compute_cycles_per_tile, weight_cycles_per_tile)
    producer_total_cycles = hidden_load_cycles + compute_cycles_per_tile + max(0, tile_count - 1) * producer_ii_cycles
    ranker = _choose_ranker(
        producer_ii_cycles=producer_ii_cycles,
        thresholds=thresholds,
        costs=costs,
    )
    return {
        "vocab_size": vocab_size,
        "hidden_size": hidden_size,
        "producer_lanes": producer_lanes,
        "tile_count": tile_count,
        "macs_per_cycle": macs_per_cycle,
        "memory_bandwidth_bytes_per_cycle": memory_bandwidth_bytes_per_cycle,
        "weight_cache_hit_rate": weight_cache_hit_rate,
        "weight_bits": weight_bits,
        "activation_bits": activation_bits,
        "macs_per_tile": macs_per_tile,
        "weight_bytes_per_tile": weight_bytes_per_tile,
        "charged_weight_bytes_per_tile": charged_weight_bytes_per_tile,
        "hidden_bytes_per_token": hidden_bytes_per_token,
        "compute_cycles_per_tile": compute_cycles_per_tile,
        "weight_cycles_per_tile": weight_cycles_per_tile,
        "hidden_load_cycles": hidden_load_cycles,
        "producer_ii_cycles": producer_ii_cycles,
        "producer_total_cycles": producer_total_cycles,
        "producer_latency_us_per_token": round(producer_total_cycles * clock_ns / 1000.0, 6),
        "service_limiter": "weight_memory" if weight_cycles_per_tile >= compute_cycles_per_tile else "compute_array",
        "selected_ranker": ranker,
    }


def build_report(
    *,
    serial_ranker: JsonDict,
    producer_replay: JsonDict,
    promoted_wrapper: JsonDict | None,
    vocab_size_list: list[int],
    hidden_size_list: list[int],
    producer_lanes_list: list[int],
    macs_per_cycle_list: list[int],
    memory_bandwidth_bytes_per_cycle_list: list[float],
    weight_cache_hit_rate_list: list[float],
    weight_bits: int,
    activation_bits: int,
    clock_ns: float,
) -> JsonDict:
    thresholds = _replay_thresholds(producer_replay)
    costs = _ranker_costs(serial_ranker)
    rows: list[JsonDict] = []
    for vocab_size in vocab_size_list:
        for hidden_size in hidden_size_list:
            for producer_lanes in producer_lanes_list:
                for macs_per_cycle in macs_per_cycle_list:
                    for bandwidth in memory_bandwidth_bytes_per_cycle_list:
                        for hit_rate in weight_cache_hit_rate_list:
                            rows.append(
                                _cadence_row(
                                    vocab_size=vocab_size,
                                    hidden_size=hidden_size,
                                    producer_lanes=producer_lanes,
                                    macs_per_cycle=macs_per_cycle,
                                    memory_bandwidth_bytes_per_cycle=bandwidth,
                                    weight_cache_hit_rate=hit_rate,
                                    weight_bits=weight_bits,
                                    activation_bits=activation_bits,
                                    clock_ns=clock_ns,
                                    thresholds=thresholds,
                                    costs=costs,
                                )
                            )

    risky_rows = [
        row
        for row in rows
        if (row.get("selected_ranker") or {}).get("decision") != "serial_ranker_safe"
    ]
    promoted = (
        (promoted_wrapper or {}).get("decision", {}).get("decision")
        if isinstance(promoted_wrapper, dict)
        else None
    )
    return {
        "version": 0.1,
        "model": "decoder_output_projection_cadence_sensitivity_v1",
        "inputs": {
            "vocab_size_list": vocab_size_list,
            "hidden_size_list": hidden_size_list,
            "producer_lanes_list": producer_lanes_list,
            "macs_per_cycle_list": macs_per_cycle_list,
            "memory_bandwidth_bytes_per_cycle_list": memory_bandwidth_bytes_per_cycle_list,
            "weight_cache_hit_rate_list": weight_cache_hit_rate_list,
            "weight_bits": weight_bits,
            "activation_bits": activation_bits,
            "clock_ns": clock_ns,
        },
        "ranker_zero_backpressure_thresholds": thresholds,
        "ranker_costs": costs,
        "promoted_wrapper_decision": promoted,
        "cadence_sweep": rows,
        "risk_summary": {
            "total_rows": len(rows),
            "serial_safe_rows": len(rows) - len(risky_rows),
            "serial_unsafe_rows": len(risky_rows),
            "unsafe_examples": risky_rows[:12],
        },
        "recommendation": {
            "decision": "resident_weight_can_outpace_serial_ranker" if risky_rows else "serial_ranker_safe_across_sweep",
            "next_step": (
                "Measure or model producer output cadence under resident/cache-backed output weights. "
                "If cadence approaches the unsafe rows, evaluate a buffered or rank-tree producer-coupled wrapper."
                if risky_rows
                else "Keep serial_lpc1 as the selected producer-coupled ranker while moving to measured producer traces."
            ),
        },
        "assumptions": [
            "weight_cache_hit_rate reduces output-projection weight bytes charged per tile; 1.0 is a resident-weight bound.",
            "compute_cycles_per_tile still charges producer_lanes * hidden_size MACs per tile.",
            "Ranker safety uses replay-observed zero-backpressure thresholds, not only analytical service cycles.",
            "The model does not add buffering between producer and ranker; buffering could absorb bursty faster producer rows.",
        ],
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Cadence Sensitivity",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['recommendation']['decision']}`",
        f"- serial_safe_rows: `{payload['risk_summary']['serial_safe_rows']}/{payload['risk_summary']['total_rows']}`",
        f"- next_step: {payload['recommendation']['next_step']}",
        "",
        "## Ranker Thresholds",
        "",
        "| ranker | min zero-backpressure II | service cycles |",
        "|---|---:|---:|",
    ]
    for row in sorted(payload["ranker_zero_backpressure_thresholds"].values(), key=lambda item: item["lanes_per_cycle"]):
        lines.append(
            f"| {row['ranker']} | {row['min_zero_backpressure_ii_cycles']} | {row['ranker_service_cycles']} |"
        )

    lines.extend(
        [
            "",
            "## Cadence Sweep",
            "",
            "| vocab | hidden | W | MAC/cycle | BW | hit | prod II | limiter | selected ranker | decision |",
            "|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
        ]
    )
    for row in payload["cadence_sweep"][:96]:
        selected = row["selected_ranker"]
        lines.append(
            "| {vocab} | {hidden} | {lanes} | {macs} | {bw} | {hit} | {ii} | {limiter} | {ranker} | {decision} |".format(
                vocab=row["vocab_size"],
                hidden=row["hidden_size"],
                lanes=row["producer_lanes"],
                macs=row["macs_per_cycle"],
                bw=row["memory_bandwidth_bytes_per_cycle"],
                hit=row["weight_cache_hit_rate"],
                ii=row["producer_ii_cycles"],
                limiter=row["service_limiter"],
                ranker=selected.get("ranker"),
                decision=selected.get("decision"),
            )
        )

    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serial-ranker", required=True)
    ap.add_argument("--producer-replay", required=True)
    ap.add_argument("--promoted-wrapper")
    ap.add_argument("--vocab-size-list", type=_int_list, default=[50257, 100000])
    ap.add_argument("--hidden-size-list", type=_int_list, default=[768, 2048])
    ap.add_argument("--producer-lanes-list", type=_int_list, default=[64, 128])
    ap.add_argument("--macs-per-cycle-list", type=_int_list, default=[8192, 32768])
    ap.add_argument("--memory-bandwidth-bytes-per-cycle-list", type=_int_list, default=[64, 256])
    ap.add_argument("--weight-cache-hit-rate-list", type=_float_list, default=[0.0, 0.5, 0.9, 1.0])
    ap.add_argument("--weight-bits", type=int, default=16)
    ap.add_argument("--activation-bits", type=int, default=16)
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        serial_ranker=_load_json(args.serial_ranker),
        producer_replay=_load_json(args.producer_replay),
        promoted_wrapper=_load_json(args.promoted_wrapper) if args.promoted_wrapper else None,
        vocab_size_list=args.vocab_size_list,
        hidden_size_list=args.hidden_size_list,
        producer_lanes_list=args.producer_lanes_list,
        macs_per_cycle_list=args.macs_per_cycle_list,
        memory_bandwidth_bytes_per_cycle_list=[float(x) for x in args.memory_bandwidth_bytes_per_cycle_list],
        weight_cache_hit_rate_list=args.weight_cache_hit_rate_list,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        clock_ns=args.clock_ns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compare measured r64 ranker service points against producer tile cadence."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

RANKER_TILE_LANES = 64


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _maybe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _maybe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def _placed_cell_area(variant: JsonDict) -> float | None:
    synthesis = variant.get("synthesis") if isinstance(variant.get("synthesis"), dict) else {}
    for line in synthesis.get("log_tail", []):
        match = re.search(r"Placed Cell Area\s+([0-9.]+)", str(line))
        if match:
            return float(match.group(1))
    metrics = variant.get("metrics_row") if isinstance(variant.get("metrics_row"), dict) else {}
    return _maybe_float(metrics.get("placed_cell_area"))


def _metrics(variant: JsonDict) -> JsonDict:
    metrics = variant.get("metrics_row") if isinstance(variant.get("metrics_row"), dict) else {}
    return {
        "critical_path_ns": _maybe_float(metrics.get("critical_path_ns")),
        "die_area_um2": _maybe_float(metrics.get("die_area")),
        "placed_cell_area_um2": _placed_cell_area(variant),
        "total_power_mw": _maybe_float(metrics.get("total_power_mw")),
        "stage_elapsed_seconds": _maybe_float(metrics.get("stage_elapsed_seconds")),
    }


def _serial_ranker_points(payload: JsonDict) -> list[JsonDict]:
    points: list[JsonDict] = []
    for variant in payload.get("variants", []):
        if not isinstance(variant, dict) or variant.get("status") != "ok":
            continue
        lanes = _maybe_int(variant.get("lanes_per_cycle"))
        scan_cycles = _maybe_int(variant.get("tile_scan_cycles"))
        ii_cycles = _maybe_int(variant.get("ii_goal_cycles"))
        if lanes is None or scan_cycles is None:
            continue
        points.append(
            {
                "ranker": f"serial_lpc{lanes}",
                "family": "serial_running_best",
                "lanes_per_cycle": lanes,
                "tile_scan_cycles": scan_cycles,
                "tile_service_cycles": ii_cycles or (scan_cycles + 1),
                "pipeline_tail_cycles": 0,
                "source_top": variant.get("top"),
                **_metrics(variant),
            }
        )
    return points


def _rank_tree_points(payload: JsonDict) -> list[JsonDict]:
    points: list[JsonDict] = []
    for variant in payload.get("variants", []):
        if not isinstance(variant, dict) or variant.get("status") != "ok":
            continue
        radix = _maybe_int(variant.get("radix"))
        stages = _maybe_int(variant.get("pipeline_stages")) or 0
        if radix is None:
            continue
        points.append(
            {
                "ranker": f"ranktree_radix{radix}",
                "family": "fully_parallel_rank_tree",
                "radix": radix,
                "tile_scan_cycles": 1,
                "tile_service_cycles": 1,
                "pipeline_tail_cycles": stages,
                "source_top": variant.get("top"),
                **_metrics(variant),
            }
        )
    return points


def _ranker_points(serial_ranker: JsonDict, rank_tree: JsonDict) -> list[JsonDict]:
    return _serial_ranker_points(serial_ranker) + _rank_tree_points(rank_tree)


def _coupled_cycles(
    *,
    producer_latency_cycles: int,
    producer_ii_cycles: int,
    tile_count: int,
    ranker_service_cycles: int,
    ranker_tail_cycles: int,
) -> tuple[int, int]:
    previous_finish = 0
    max_wait = 0
    for index in range(tile_count):
        arrival = producer_latency_cycles + index * producer_ii_cycles
        start = max(arrival, previous_finish)
        max_wait = max(max_wait, start - arrival)
        previous_finish = start + ranker_service_cycles
    return previous_finish + ranker_tail_cycles, max_wait


def build_report(
    *,
    producer_service: JsonDict,
    serial_ranker: JsonDict,
    rank_tree: JsonDict,
) -> JsonDict:
    rankers = _ranker_points(serial_ranker, rank_tree)
    clock_ns = float(producer_service.get("inputs", {}).get("clock_ns", 1.0))
    rows: list[JsonDict] = []
    for producer in producer_service.get("producer_service_sweep", []):
        if not isinstance(producer, dict):
            continue
        producer_lanes = _maybe_int(producer.get("producer_lanes"))
        producer_ii = _maybe_int(producer.get("producer_ii_cycles"))
        producer_latency = _maybe_int(producer.get("producer_latency_cycles"))
        tile_count = _maybe_int(producer.get("tile_count"))
        if producer_lanes is None or producer_ii is None or producer_latency is None or tile_count is None:
            continue
        producer_done = producer_latency + max(0, tile_count - 1) * producer_ii
        lanes_ratio = _ceil_div(producer_lanes, RANKER_TILE_LANES)
        for ranker in rankers:
            for integration in ("single_r64_ranker", "banked_r64_rankers"):
                if lanes_ratio == 1 and integration == "banked_r64_rankers":
                    continue
                instance_count = 1 if integration == "single_r64_ranker" else lanes_ratio
                service_scale = lanes_ratio if integration == "single_r64_ranker" else 1
                service_cycles = int(ranker["tile_service_cycles"]) * service_scale
                coupled_cycles, max_wait_cycles = _coupled_cycles(
                    producer_latency_cycles=producer_latency,
                    producer_ii_cycles=producer_ii,
                    tile_count=tile_count,
                    ranker_service_cycles=service_cycles,
                    ranker_tail_cycles=int(ranker["pipeline_tail_cycles"]),
                )
                throughput_margin = producer_ii - service_cycles
                throughput_ok = throughput_margin >= 0
                total_power = (
                    None
                    if ranker.get("total_power_mw") is None
                    else ranker["total_power_mw"] * instance_count
                )
                placed_area = (
                    None
                    if ranker.get("placed_cell_area_um2") is None
                    else ranker["placed_cell_area_um2"] * instance_count
                )
                rows.append(
                    {
                        "scenario": producer.get("scenario"),
                        "vocab_size": producer.get("vocab_size"),
                        "hidden_size": producer.get("hidden_size"),
                        "producer_lanes": producer_lanes,
                        "tile_count": tile_count,
                        "macs_per_cycle": producer.get("macs_per_cycle"),
                        "memory_bandwidth_bytes_per_cycle": producer.get(
                            "memory_bandwidth_bytes_per_cycle"
                        ),
                        "producer_ii_cycles": producer_ii,
                        "producer_latency_cycles": producer_latency,
                        "producer_done_cycles": producer_done,
                        "producer_latency_us_per_token": producer.get(
                            "producer_latency_us_per_token"
                        ),
                        "service_limiter": producer.get("service_limiter"),
                        "ranker": ranker["ranker"],
                        "ranker_family": ranker["family"],
                        "integration": integration,
                        "ranker_instances": instance_count,
                        "ranker_tile_service_cycles": ranker["tile_service_cycles"],
                        "ranker_service_cycles_per_producer_tile": service_cycles,
                        "ranker_pipeline_tail_cycles": ranker["pipeline_tail_cycles"],
                        "throughput_ok": throughput_ok,
                        "throughput_margin_cycles": throughput_margin,
                        "ranker_utilization": round(service_cycles / producer_ii, 6),
                        "max_ranker_wait_cycles": max_wait_cycles,
                        "coupled_total_cycles": coupled_cycles,
                        "coupled_latency_us_per_token": round(
                            coupled_cycles * clock_ns / 1000.0, 6
                        ),
                        "coupled_extra_cycles_after_producer": max(0, coupled_cycles - producer_done),
                        "ranker_critical_path_ns": ranker.get("critical_path_ns"),
                        "ranker_total_power_mw": total_power,
                        "ranker_placed_cell_area_um2": placed_area,
                    }
                )

    feasible_rows = [row for row in rows if row["throughput_ok"]]
    low_power_feasible = (
        min(
            feasible_rows,
            key=lambda row: (
                row["ranker_total_power_mw"] is None,
                row["ranker_total_power_mw"] or math.inf,
                row["ranker_placed_cell_area_um2"] or math.inf,
                row["ranker_service_cycles_per_producer_tile"],
            ),
        )
        if feasible_rows
        else None
    )
    latency_best = (
        min(
            rows,
            key=lambda row: (
                row["coupled_latency_us_per_token"],
                not row["throughput_ok"],
                row["ranker_total_power_mw"] or math.inf,
            ),
        )
        if rows
        else None
    )
    return {
        "version": 0.1,
        "model": "decoder_producer_ranker_service_compatibility_v1",
        "target": {
            "producer_model": producer_service.get("model"),
            "ranker_tile_lanes": RANKER_TILE_LANES,
            "ranker_sources": [serial_ranker.get("model"), rank_tree.get("model")],
        },
        "assumptions": [
            "Producer rows are the existing stage-serialized output-projection service model.",
            "Ranker service is measured at r64/k1 and compared to producer tile arrival cadence.",
            "single_r64_ranker scans wider producer tiles sequentially through one r64 ranker.",
            "banked_r64_rankers assumes one measured r64 ranker instance per 64 producer lanes.",
            "throughput_ok means ranker service for one producer tile is no slower than producer_ii_cycles.",
            "This is a service-time compatibility model; it does not replace ready-valid RTL equivalence.",
        ],
        "ranker_points": rankers,
        "compatibility_sweep": rows,
        "recommendation": {
            "decision": (
                "serial_ranker_service_compatible" if feasible_rows else "ranker_service_bottleneck"
            ),
            "lowest_power_feasible": low_power_feasible,
            "latency_best": latency_best,
            "next_step": (
                "Promote the lowest-power feasible serial point into producer-coupled RTL if "
                "the selected producer cadence remains memory-limited; otherwise retain the "
                "latency-best rank tree for a compute-dense producer."
            ),
        },
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    rec = payload["recommendation"]
    lines = [
        "# Decoder Producer/Ranker Service Compatibility",
        "",
        f"- decision: `{rec['decision']}`",
    ]
    if rec.get("lowest_power_feasible"):
        row = rec["lowest_power_feasible"]
        lines.append(
            "- lowest_power_feasible: "
            f"`{row['ranker']} {row['integration']} W{row['producer_lanes']} "
            f"II{row['producer_ii_cycles']} service{row['ranker_service_cycles_per_producer_tile']}`"
        )
    if rec.get("latency_best"):
        row = rec["latency_best"]
        lines.append(
            "- latency_best: "
            f"`{row['ranker']} {row['integration']} W{row['producer_lanes']} "
            f"{row['coupled_latency_us_per_token']}us`"
        )
    lines.extend(
        [
            "",
            "## Compatibility Sweep",
            "",
            "| ranker | integration | vocab | hidden | W | MAC/cycle | BW | prod II | service | margin | util | ok | extra cycles | power mW | placed area |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
        ]
    )
    focus_rows = sorted(
        payload["compatibility_sweep"],
        key=lambda row: (
            row["vocab_size"],
            row["hidden_size"],
            row["producer_lanes"],
            row["macs_per_cycle"],
            row["memory_bandwidth_bytes_per_cycle"],
            row["integration"],
            row["ranker"],
        ),
    )
    for row in focus_rows[:80]:
        lines.append(
            "| {ranker} | {integration} | {vocab} | {hidden} | {lanes} | {macs} | {bw} | {ii} | {service} | {margin} | {util} | `{ok}` | {extra} | {power} | {area} |".format(
                ranker=row["ranker"],
                integration=row["integration"],
                vocab=row["vocab_size"],
                hidden=row["hidden_size"],
                lanes=row["producer_lanes"],
                macs=row["macs_per_cycle"],
                bw=row["memory_bandwidth_bytes_per_cycle"],
                ii=row["producer_ii_cycles"],
                service=row["ranker_service_cycles_per_producer_tile"],
                margin=row["throughput_margin_cycles"],
                util=row["ranker_utilization"],
                ok=row["throughput_ok"],
                extra=row["coupled_extra_cycles_after_producer"],
                power=row["ranker_total_power_mw"],
                area=row["ranker_placed_cell_area_um2"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for assumption in payload["assumptions"]:
        lines.append(f"- {assumption}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--producer-service", required=True)
    ap.add_argument("--serial-ranker", required=True)
    ap.add_argument("--rank-tree", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_report(
        producer_service=_load_json(Path(args.producer_service)),
        serial_ranker=_load_json(Path(args.serial_ranker)),
        rank_tree=_load_json(Path(args.rank_tree)),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": str(out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

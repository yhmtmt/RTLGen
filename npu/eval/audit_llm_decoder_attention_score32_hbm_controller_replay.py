#!/usr/bin/env python3
"""Deterministic cycle-level replay of score32 HBM traffic for the schedule wrapper frontier.

This model replaces the analytic row-hit model with a deterministic burst scheduler over
channels, fixed row-window state, request overhead, row-miss penalty, scheduler gap, and a
global outstanding request window.
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_int_list(value: str) -> list[int]:
    parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed:
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    if any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("all values must be strictly positive")
    return parsed


def _parse_int_list_optional_zero(value: str) -> list[int]:
    parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed:
        raise argparse.ArgumentTypeError("expected comma-separated integers")
    if any(item < 0 for item in parsed):
        raise argparse.ArgumentTypeError("all values must be non-negative")
    return parsed


def _parse_float_list(value: str) -> list[float]:
    parsed = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed:
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    if any(item <= 0.0 for item in parsed):
        raise argparse.ArgumentTypeError("all values must be strictly positive")
    return parsed


def _parse_float_list_01(value: str) -> list[float]:
    parsed = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed:
        raise argparse.ArgumentTypeError("expected comma-separated floats")
    if any(item < 0.0 or item > 1.0 for item in parsed):
        raise argparse.ArgumentTypeError("all values must be in [0,1]")
    return parsed


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _clamp(v: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, v))


def _pick_row(payload: JsonDict, keys: tuple[str, ...]) -> JsonDict:
    for key in keys:
        row = _as_dict(payload.get(key))
        if row:
            return row
    return {}


def _find_score32_best_latency(payload: JsonDict) -> JsonDict:
    return _pick_row(payload, ("best_latency", "best", "best_requested", "best_feasible"))


def _find_score32_best_requested(payload: JsonDict) -> JsonDict:
    return _pick_row(payload, ("best_requested", "best_area_fit", "best_feasible", "best"))


def _tile_hbm_bytes(physical_row: JsonDict, source_row: JsonDict) -> int:
    full_tile_bytes = _as_float(physical_row.get("onchip_full_tile_bytes"), 0.0)
    if full_tile_bytes <= 0.0:
        full_tile_bytes = _as_float(physical_row.get("tile_bytes"), _as_float(source_row.get("onchip_full_tile_bytes"), 0.0))
    byte_share = _as_float(physical_row.get("hbm_byte_share"), _as_float(source_row.get("hbm_byte_share"), 1.0))
    byte_share = _clamp(byte_share, 0.0, 1.0)
    if full_tile_bytes <= 0.0:
        full_tile_bytes = 1024.0 * 1024.0
    return max(1, int(math.ceil(full_tile_bytes * byte_share)))


def _build_burst_stream(
    *,
    tile_hbm_bytes: int,
    burst_bytes: int,
    channel_count: int,
    row_span_bursts: int,
    row_hit_rate: float,
) -> tuple[list[int], list[bool], int, int]:
    burst_count = _ceil_div(tile_hbm_bytes, max(1, burst_bytes))
    if burst_count == 0:
        return [], [], 0, 0

    channels = [i % channel_count for i in range(burst_count)]
    per_channel_burst_idx = [0] * channel_count
    per_channel_row = [-1] * channel_count
    row_span = max(1, row_span_bursts)
    miss_flags = [False] * burst_count

    for burst_idx, ch in enumerate(channels):
        row_idx = per_channel_burst_idx[ch] // row_span
        if per_channel_row[ch] != row_idx:
            miss_flags[burst_idx] = True
            per_channel_row[ch] = row_idx
        per_channel_burst_idx[ch] += 1

    deterministic_miss_count = sum(miss_flags)
    target_hit_rate = _clamp(row_hit_rate, 0.0, 1.0)
    target_miss_count = int(math.ceil(burst_count * (1.0 - target_hit_rate)))
    required_miss_count = max(deterministic_miss_count, target_miss_count)

    added = 0
    if required_miss_count > deterministic_miss_count:
        for i in range(burst_count):
            if added + deterministic_miss_count >= required_miss_count:
                break
            if not miss_flags[i]:
                miss_flags[i] = True
                added += 1

    final_miss_count = sum(miss_flags)
    return channels, miss_flags, burst_count, final_miss_count


def _simulate_replay_cycles(
    *,
    channel_count: int,
    channel_bandwidth_bytes_per_cycle: float,
    burst_bytes: int,
    channels: list[int],
    miss_flags: list[bool],
    request_overhead_cycles: int,
    row_miss_penalty_cycles: int,
    scheduler_gap_cycles: int,
    outstanding: int,
    scheduler_efficiency: float,
) -> int:
    burst_count = len(channels)
    if burst_count == 0:
        return 0

    effective_bw = max(1.0, float(channel_bandwidth_bytes_per_cycle) * _clamp(scheduler_efficiency, 0.01, 1.0))
    payload_cycle_per_burst = _ceil_div(burst_bytes, effective_bw)
    channel_ready = [0.0] * channel_count
    active: list[float] = []
    now = 0.0

    for burst_idx, ch in enumerate(channels):
        base_cycles = payload_cycle_per_burst + int(request_overhead_cycles) + int(scheduler_gap_cycles)
        miss_cycles = int(row_miss_penalty_cycles) if miss_flags[burst_idx] else 0
        burst_cycles = base_cycles + miss_cycles

        while True:
            while active and active[0] <= now:
                heapq.heappop(active)
            start = max(now, channel_ready[ch])
            while active and active[0] <= start:
                heapq.heappop(active)
            if len(active) < max(1, outstanding):
                break
            now = active[0]

        finish = start + burst_cycles
        channel_ready[ch] = finish
        heapq.heappush(active, finish)

    while active:
        now = heapq.heappop(active)
    return int(math.ceil(now))


def _build_replay_row(
    *,
    source_row: JsonDict,
    source_latency_us: float,
    source_tile_hbm_cycles: int,
    source_tile_service_cycles: int,
    compute_power_mw: float,
    hbm_energy_mj_per_token: float,
    die_area_mm2: float,
    compute_area_mm2: float,
    macs_per_cycle: float,
    tile_hbm_bytes: int,
    channel_count: int,
    channel_bandwidth_bytes_per_cycle: float,
    burst_bytes: int,
    row_span_bursts: int,
    row_hit_rate: float,
    request_overhead_cycles: int,
    row_miss_penalty_cycles: int,
    hbm_outstanding: int,
    scheduler_gap_cycles: int,
    scheduler_efficiency: float,
) -> JsonDict:
    channels, miss_flags, burst_count, miss_count = _build_burst_stream(
        tile_hbm_bytes=tile_hbm_bytes,
        burst_bytes=burst_bytes,
        channel_count=channel_count,
        row_span_bursts=row_span_bursts,
        row_hit_rate=row_hit_rate,
    )

    replay_service_cycles = _simulate_replay_cycles(
        channel_count=channel_count,
        channel_bandwidth_bytes_per_cycle=channel_bandwidth_bytes_per_cycle,
        burst_bytes=burst_bytes,
        channels=channels,
        miss_flags=miss_flags,
        request_overhead_cycles=request_overhead_cycles,
        row_miss_penalty_cycles=row_miss_penalty_cycles,
        scheduler_gap_cycles=scheduler_gap_cycles,
        outstanding=hbm_outstanding,
        scheduler_efficiency=scheduler_efficiency,
    )

    dominant_source_cycles = max(1, source_tile_hbm_cycles, source_tile_service_cycles)
    hbm_excess_cycles = max(0, replay_service_cycles - dominant_source_cycles)
    tile_waves = max(1, _as_int(source_row.get("tile_waves"), 1))
    layers = max(1, _as_int(source_row.get("layers"), 32))
    clock_ns = _as_float(source_row.get("clock_ns"), 1.0)
    added_latency_us = hbm_excess_cycles * tile_waves * layers * clock_ns / 1000.0
    replay_latency_us = source_latency_us + added_latency_us
    compute_energy_mj = compute_power_mw * replay_latency_us * 1e-6
    total_energy_mj = hbm_energy_mj_per_token + compute_energy_mj

    return {
        "candidate_id": "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best",
        "family": "score32_exp_lut_div",
        "source_artifact": "score32_schedule_wrapper_hbm_controller_replay",
        "precision_status": "mixed_int8_generation_quality_pass",
        "quality_backed": True,
        "promotable": True,
        "die_area_mm2": round(die_area_mm2, 6),
        "compute_area_mm2": round(compute_area_mm2, 6),
        "macs_per_cycle": round(macs_per_cycle, 6),
        "channel_count": channel_count,
        "channel_bandwidth_bytes_per_cycle": round(_as_float(channel_bandwidth_bytes_per_cycle), 6),
        "burst_bytes": burst_bytes,
        "row_span_bursts": row_span_bursts,
        "row_hit_rate": row_hit_rate,
        "request_overhead_cycles": request_overhead_cycles,
        "row_miss_penalty_cycles": row_miss_penalty_cycles,
        "hbm_outstanding": hbm_outstanding,
        "scheduler_gap_cycles": scheduler_gap_cycles,
        "scheduler_efficiency": round(_as_float(scheduler_efficiency), 6),
        "tile_hbm_bytes": tile_hbm_bytes,
        "burst_count": burst_count,
        "deterministic_row_miss_count": miss_count,
        "replay_service_cycles": replay_service_cycles,
        "source_tile_hbm_cycles": source_tile_hbm_cycles,
        "source_tile_service_cycles": source_tile_service_cycles,
        "dominant_source_cycles": dominant_source_cycles,
        "hbm_excess_cycles": hbm_excess_cycles,
        "replay_effective_hbm_bytes_per_cycle": round(tile_hbm_bytes / max(1, replay_service_cycles), 6),
        "hbm_added_latency_us": round(added_latency_us, 6),
        "source_latency_us": round(source_latency_us, 6),
        "latency_us": round(replay_latency_us, 6),
        "token_throughput_per_s": round(1_000_000.0 / replay_latency_us, 9) if replay_latency_us > 0.0 else 0.0,
        "hbm_dominates_tile": replay_service_cycles > dominant_source_cycles,
        "compute_power_mw": round(compute_power_mw, 6),
        "compute_energy_mj_per_token": round(compute_energy_mj, 9),
        "hbm_energy_mj_per_token": round(hbm_energy_mj_per_token, 9),
        "total_energy_mj_per_token": round(total_energy_mj, 9),
        "remaining_abstractions": [
            "controller replay is deterministic cycle-level but not RTL-timing accurate",
            "does not include vendor HBM current signoff",
        ],
    }


def _hbm_energy_from_source(row: JsonDict) -> float:
    if not row:
        return 0.0
    direct = _as_float(row.get("hbm_energy_mj_per_token"))
    if direct > 0.0:
        return direct
    command = _as_dict(row.get("hbm_command_calibrated_energy"))
    return _as_float(command.get("energy_mj"), direct)


def build_report(args: argparse.Namespace) -> JsonDict:
    hbm_closure = _load_json(args.score32_hbm_dram_service_json)
    physical = _load_json(args.score32_physical_feasibility_json)

    closure_row = _find_score32_best_latency(hbm_closure)
    if not closure_row:
        raise ValueError("score32 HBM closure JSON has no best-latency row")

    physical_row = _find_score32_best_requested(physical)
    if not physical_row:
        raise ValueError("score32 physical feasibility JSON has no best_requested-style row")

    tile_hbm_bytes = _tile_hbm_bytes(physical_row=physical_row, source_row=closure_row)
    hbm_energy_mj_per_token = _hbm_energy_from_source(closure_row)
    source_latency_us = _as_float(
        physical_row.get("replica_recost_latency_us") or closure_row.get("source_latency_us") or closure_row.get("latency_us")
    )
    source_tile_hbm_cycles = _as_int(
        physical_row.get("tile_hbm_cycles")
        or physical_row.get("controller_service_cycles")
        or physical_row.get("onchip_hbm_cycles_inherited"),
        1,
    )
    source_tile_service_cycles = _as_int(
        physical_row.get("replica_recost_tile_service_cycles")
        or physical_row.get("tile_service_cycles")
        or source_tile_hbm_cycles,
        1,
    )

    compute_power_mw = _as_float(
        physical_row.get("substituted_compute_plus_control_power_mw")
        or physical_row.get("replica_recost_compute_plus_control_power_mw")
        or physical_row.get("substituted_compute_power_mw")
        or physical_row.get("replica_recost_compute_power_mw")
        or physical_row.get("logic_power_mw")
        or closure_row.get("compute_power_mw")
        or 0.0
    )
    die_area_mm2 = _as_float(physical_row.get("die_area_mm2"), _as_float(closure_row.get("die_area_mm2"), 0.0))
    compute_area_mm2 = _as_float(
        physical_row.get("replica_recost_compute_area_um2")
        or physical_row.get("compute_area_required_um2")
        or physical_row.get("substituted_compute_area_um2")
        or physical_row.get("compute_area_um2"),
        0.0,
    ) / 1.0e6
    macs_per_cycle = _as_float(
        physical_row.get("replica_recost_macs_per_cycle")
        or physical_row.get("macs_per_cycle")
        or closure_row.get("macs_per_cycle"),
        0.0,
    )

    rows: list[JsonDict] = []
    for channel_count in args.channel_count_list:
        for channel_bw in args.channel_bandwidth_bytes_per_cycle_list:
            for burst_bytes in args.burst_bytes_list:
                for row_span in args.row_span_bursts_list:
                    for row_hit_rate in args.row_hit_rate_list:
                        for overhead in args.request_overhead_cycles_list:
                            for miss_penalty in args.row_miss_penalty_cycles_list:
                                for hbm_outstanding in args.hbm_outstanding_list:
                                    for scheduler_gap in args.scheduler_gap_cycles_list:
                                        for sched_eff in args.scheduler_efficiency_list:
                                            rows.append(
                                                _build_replay_row(
                                                    source_row=physical_row,
                                                    source_latency_us=source_latency_us,
                                                    source_tile_hbm_cycles=max(1, source_tile_hbm_cycles),
                                                    source_tile_service_cycles=max(1, source_tile_service_cycles),
                                                    compute_power_mw=compute_power_mw,
                                                    hbm_energy_mj_per_token=hbm_energy_mj_per_token,
                                                    die_area_mm2=die_area_mm2,
                                                    compute_area_mm2=compute_area_mm2,
                                                    macs_per_cycle=macs_per_cycle,
                                                    tile_hbm_bytes=tile_hbm_bytes,
                                                    channel_count=max(1, int(channel_count)),
                                                    channel_bandwidth_bytes_per_cycle=float(channel_bw),
                                                    burst_bytes=max(1, int(burst_bytes)),
                                                    row_span_bursts=max(1, int(row_span)),
                                                    row_hit_rate=float(row_hit_rate),
                                                    request_overhead_cycles=max(0, int(overhead)),
                                                    row_miss_penalty_cycles=max(0, int(miss_penalty)),
                                                    hbm_outstanding=max(1, int(hbm_outstanding)),
                                                    scheduler_gap_cycles=max(0, int(scheduler_gap)),
                                                    scheduler_efficiency=float(sched_eff),
                                                )
                                            )

    rows_sorted = sorted(rows, key=lambda row: (row["latency_us"], row["total_energy_mj_per_token"]))
    best_latency = rows_sorted[0]
    best_energy = min(rows, key=lambda row: (row["total_energy_mj_per_token"], row["latency_us"]))

    decision = (
        "score32_hbm_controller_replay_hbm_sensitive"
        if bool(best_latency.get("hbm_dominates_tile"))
        else "score32_hbm_controller_replay_compute_dominant"
    )

    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_hbm_controller_replay_v1",
        "decision": decision,
        "inputs": {
            "score32_hbm_dram_service_json": str(args.score32_hbm_dram_service_json),
            "score32_physical_feasibility_json": str(args.score32_physical_feasibility_json),
            "channel_count_list": args.channel_count_list,
            "channel_bandwidth_bytes_per_cycle_list": args.channel_bandwidth_bytes_per_cycle_list,
            "burst_bytes_list": args.burst_bytes_list,
            "row_span_bursts_list": args.row_span_bursts_list,
            "row_hit_rate_list": args.row_hit_rate_list,
            "request_overhead_cycles_list": args.request_overhead_cycles_list,
            "row_miss_penalty_cycles_list": args.row_miss_penalty_cycles_list,
            "hbm_outstanding_list": args.hbm_outstanding_list,
            "scheduler_gap_cycles_list": args.scheduler_gap_cycles_list,
            "scheduler_efficiency_list": args.scheduler_efficiency_list,
        },
        "diagnosis": {
            "best_latency_us": best_latency["latency_us"],
            "best_latency_total_energy_mj_per_token": best_latency["total_energy_mj_per_token"],
            "best_latency_token_throughput_per_s": best_latency["token_throughput_per_s"],
            "best_latency_hbm_dominates_tile": bool(best_latency.get("hbm_dominates_tile")),
            "best_latency_row_miss_count": best_latency["deterministic_row_miss_count"],
            "best_energy_us": best_energy["latency_us"],
            "best_energy_total_energy_mj_per_token": best_energy["total_energy_mj_per_token"],
            "best_energy_hbm_service_cycles": best_energy["replay_service_cycles"],
            "best_requested_row_latency_us": source_latency_us,
            "hbm_energy_source": hbm_energy_mj_per_token,
            "compute_power_mw_source": compute_power_mw,
            "row_count": len(rows),
            "remaining_abstractions": [
                "controller replay is deterministic cycle-level, not RTL timing",
                "vendor HBM current signoff is not represented",
            ],
        },
        "best_latency": best_latency,
        "best_energy": best_energy,
        "top_rows": rows_sorted[: args.top_k],
        "assumptions": [
            "Replay builds a deterministic burst stream with round-robin channel interleave.",
            "Each channel has row-window state with misses determined by row_span_bursts and adjusted to hit_rate.",
            "Per-request cycles include burst transfer payload, request overhead, row-miss penalty, and scheduler gap.",
            "Outstanding requests are enforced as a global in-flight limit.",
            "Replay latency is added to the schedule-wrapper recost source latency by mapping replay-cycle delta vs source HBM/service cycles.",
            "HBM energy is inherited from the score32 HBM closure; compute energy is rebuilt from physical wrapper compute power.",
        ],
        "next_step": {
            "requires_cycle_accurate_hbm_controller_rtl": True,
            "requires_vendor_hbm_current_signoff": True,
            "recommended_next_step": (
                "Use this deterministic replay as the current schedule-wrapper HBM abstraction, then replace with "
                "cycle-accurate controller timing before collapsing HBM abstraction for final frontier ranking."
            ),
        },
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best_latency"]
    diagnosis = payload["diagnosis"]
    lines = [
        "# Score32 HBM Controller Replay",
        "",
        f"- decision: `{payload['decision']}`",
        f"- best latency us: `{diagnosis['best_latency_us']}`",
        f"- best throughput token/s: `{diagnosis['best_latency_token_throughput_per_s']}`",
        f"- best latency total energy mJ/token: `{diagnosis['best_latency_total_energy_mj_per_token']}`",
        f"- best hbm-dominant: `{diagnosis['best_latency_hbm_dominates_tile']}`",
        "",
        "## Best Replay Row",
        "",
        "| ch | ch B/cyc | burst | row span | miss penalty | miss count | overhead | out | gap | row hit | eff | service cyc | added us | latency us | throughput |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {channel_count} | {channel_bandwidth_bytes_per_cycle} | {burst_bytes} | {row_span_bursts} | {row_miss_penalty_cycles} | {deterministic_row_miss_count} | {request_overhead_cycles} | {hbm_outstanding} | {scheduler_gap_cycles} | {row_hit_rate} | {scheduler_efficiency} | {replay_service_cycles} | {hbm_added_latency_us} | {latency_us} | {token_throughput_per_s} |".format(
            **best
        ),
        "",
        "## Top 10",
        "",
        "| rank | latency us | total energy | throughput | channels | out | burst | row span | misses | service cyc |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for i, row in enumerate(payload["top_rows"][:10], start=1):
        lines.append(
            "| {rank} | {latency_us} | {total_energy_mj_per_token} | {token_throughput_per_s} | {channel_count} | {hbm_outstanding} | {burst_bytes} | {row_span_bursts} | {deterministic_row_miss_count} | {replay_service_cycles} |".format(
                rank=i,
                **row,
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score32-hbm-dram-service-json", type=Path, required=True)
    parser.add_argument("--score32-physical-feasibility-json", type=Path, required=True)
    parser.add_argument(
        "--channel-count",
        "--channel-count-list",
        dest="channel_count_list",
        type=_parse_int_list,
        default=[4, 8],
    )
    parser.add_argument(
        "--channel-bandwidth-bytes-per-cycle",
        "--channel-bandwidth-bytes-per-cycle-list",
        dest="channel_bandwidth_bytes_per_cycle_list",
        type=_parse_float_list,
        default=[256.0, 512.0],
    )
    parser.add_argument(
        "--burst-bytes",
        "--burst-bytes-list",
        dest="burst_bytes_list",
        type=_parse_int_list,
        default=[256, 512],
    )
    parser.add_argument(
        "--row-span-bursts",
        "--row-span-bursts-list",
        dest="row_span_bursts_list",
        type=_parse_int_list,
        default=[1, 2, 4],
    )
    parser.add_argument(
        "--row-hit-rate",
        "--row-hit-rate-list",
        dest="row_hit_rate_list",
        type=_parse_float_list_01,
        default=[0.8, 0.95],
    )
    parser.add_argument(
        "--request-overhead-cycles",
        "--request-overhead-cycles-list",
        dest="request_overhead_cycles_list",
        type=_parse_int_list_optional_zero,
        default=[2, 4],
    )
    parser.add_argument(
        "--row-miss-penalty-cycles",
        "--row-miss-penalty-cycles-list",
        dest="row_miss_penalty_cycles_list",
        type=_parse_int_list_optional_zero,
        default=[8, 16],
    )
    parser.add_argument(
        "--hbm-outstanding",
        "--hbm-outstanding-list",
        dest="hbm_outstanding_list",
        type=_parse_int_list,
        default=[4, 8],
    )
    parser.add_argument(
        "--scheduler-gap-cycles",
        "--scheduler-gap-cycles-list",
        dest="scheduler_gap_cycles_list",
        type=_parse_int_list_optional_zero,
        default=[0, 1],
    )
    parser.add_argument(
        "--scheduler-efficiency",
        "--scheduler-efficiency-list",
        dest="scheduler_efficiency_list",
        type=_parse_float_list,
        default=[0.75, 0.9],
    )
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(
        json.dumps(
            {
                "ok": True,
                "decision": payload["decision"],
                "out": str(args.out),
                "best_latency_us": payload["diagnosis"]["best_latency_us"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

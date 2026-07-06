#!/usr/bin/env python3
"""Close score32 exp-LUT HBM/DRAM service accounting for the Llama7B frontier row."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_dict(value: Any) -> JsonDict:
    return dict(value) if isinstance(value, dict) else {}


def _float_list(value: str) -> list[float]:
    out = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not out or any(item <= 0.0 for item in out):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return out


def _int_list(value: str) -> list[int]:
    out = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not out or any(item <= 0 for item in out):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return out


def _ceil_div(numerator: int | float, denominator: int | float) -> int:
    if numerator <= 0:
        return 0
    return int(math.ceil(float(numerator) / max(1.0, float(denominator))))


def _source_score32_row(measured_command_control: JsonDict) -> JsonDict:
    for key in ("best_requested", "best_feasible", "best_area_fit", "best"):
        row = measured_command_control.get(key)
        if isinstance(row, dict):
            return dict(row)
    return {}


def _require_source_score32_row(measured_command_control: JsonDict) -> JsonDict:
    row = _source_score32_row(measured_command_control)
    required = (
        "onchip_full_tile_bytes",
        "tile_count",
        "layers",
        "clock_ns",
        "replica_recost_latency_us",
        "tile_hbm_cycles",
        "replica_recost_tile_service_cycles",
    )
    missing = [key for key in required if key not in row]
    if missing:
        raise ValueError(f"score32 measured-command-control row is missing required fields: {missing}")
    return row


def _calibrated_hbm_energy_params(command_calibrated: JsonDict) -> JsonDict:
    best = _as_dict(command_calibrated.get("best"))
    energy = _as_dict(best.get("hbm_command_calibrated_energy"))
    dram = _as_dict(best.get("hbm_dram_energy"))
    return {
        "read_hit_pj_per_byte": float(
            energy.get("read_hit_pj_per_byte", dram.get("read_hit_pj_per_byte", 0.0)) or 0.0
        ),
        "read_miss_pj_per_byte": float(
            energy.get("read_miss_pj_per_byte", dram.get("read_miss_pj_per_byte", 0.0)) or 0.0
        ),
        "write_pj_per_byte": float(energy.get("write_pj_per_byte", dram.get("write_pj_per_byte", 0.0)) or 0.0),
        "activate_precharge_pj_per_row": float(
            energy.get("activate_precharge_pj_per_row", dram.get("activate_precharge_pj_per_row", 0.0)) or 0.0
        ),
        "command_pj_per_burst": float(
            energy.get("command_pj_per_burst", dram.get("command_pj_per_burst", 0.0)) or 0.0
        ),
        "source": "hbm_command_calibrated_service",
    }


def _hbm_service(
    *,
    tile_hbm_bytes: float,
    channel_count: int,
    channel_bandwidth_bytes_per_cycle: float,
    burst_bytes: int,
    outstanding: int,
    request_overhead_cycles: int,
    row_hit_rate: float,
    row_miss_penalty_cycles: int,
    scheduler_efficiency: float,
) -> JsonDict:
    payload_bw = channel_count * channel_bandwidth_bytes_per_cycle * scheduler_efficiency
    payload_cycles = _ceil_div(tile_hbm_bytes, payload_bw)
    burst_count = _ceil_div(tile_hbm_bytes, burst_bytes)
    row_miss_count = int(math.ceil(burst_count * max(0.0, 1.0 - row_hit_rate)))
    overhead_cycles = _ceil_div(burst_count, outstanding) * request_overhead_cycles
    row_miss_cycles = _ceil_div(row_miss_count, outstanding) * row_miss_penalty_cycles
    controller_service_cycles = max(1, payload_cycles + overhead_cycles + row_miss_cycles)
    return {
        "tile_hbm_bytes": int(math.ceil(tile_hbm_bytes)),
        "payload_hbm_bytes_per_cycle": round(payload_bw, 6),
        "payload_cycles": payload_cycles,
        "burst_count": burst_count,
        "row_miss_count": row_miss_count,
        "overhead_cycles": overhead_cycles,
        "row_miss_cycles": row_miss_cycles,
        "controller_service_cycles": controller_service_cycles,
        "effective_hbm_bytes_per_cycle": round(tile_hbm_bytes / controller_service_cycles, 6),
    }


def _hbm_energy(
    *,
    tile_hbm_bytes: float,
    service: JsonDict,
    params: JsonDict,
    source_row: JsonDict,
) -> JsonDict:
    layers = int(source_row.get("layers", 32) or 32)
    tile_count = int(source_row.get("tile_count", 128) or 128)
    hidden_size = int(source_row.get("hidden_size", 4096) or 4096)
    attention_heads = int(source_row.get("attention_heads", 32) or 32)
    kv_heads = int(source_row.get("kv_heads", 4) or 4)
    kv_bits = int(source_row.get("kv_bits", 8) or 8)
    head_dim = max(1, hidden_size // max(1, attention_heads))
    row_hit_rate = float(service["row_hit_rate"])
    read_bytes_per_token = tile_hbm_bytes * tile_count * layers
    write_bytes_per_token = float(2 * kv_heads * head_dim * kv_bits // 8 * layers)
    hit_read = read_bytes_per_token * row_hit_rate
    miss_read = read_bytes_per_token - hit_read
    burst_bytes = max(1.0, float(service["burst_bytes"]))
    burst_count = math.ceil((read_bytes_per_token + write_bytes_per_token) / burst_bytes)
    miss_rows = math.ceil(miss_read / burst_bytes)
    read_hit_pj = hit_read * float(params["read_hit_pj_per_byte"])
    read_miss_pj = miss_read * float(params["read_miss_pj_per_byte"])
    write_pj = write_bytes_per_token * float(params["write_pj_per_byte"])
    activate_pj = miss_rows * float(params["activate_precharge_pj_per_row"])
    command_pj = burst_count * float(params["command_pj_per_burst"])
    energy_pj = read_hit_pj + read_miss_pj + write_pj + activate_pj + command_pj
    return {
        "energy_mj": round(energy_pj / 1.0e9, 9),
        "energy_pj": round(energy_pj, 6),
        "read_bytes_per_token": int(math.ceil(read_bytes_per_token)),
        "write_bytes_per_token": int(math.ceil(write_bytes_per_token)),
        "kv_write_model": {
            "layers": layers,
            "hidden_size": hidden_size,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "head_dim": head_dim,
            "kv_bits": kv_bits,
        },
        "burst_count_per_token": burst_count,
        "miss_row_count_per_token": miss_rows,
        "read_hit_pj": round(read_hit_pj, 6),
        "read_miss_pj": round(read_miss_pj, 6),
        "write_pj": round(write_pj, 6),
        "activate_precharge_pj": round(activate_pj, 6),
        "command_pj": round(command_pj, 6),
        **params,
    }


def _row_latency(
    *,
    source_row: JsonDict,
    envelope_row: JsonDict,
    service: JsonDict,
) -> JsonDict:
    source_latency = float(envelope_row["projected_latency_us_hbm_share_scaled"])
    source_tile_hbm_cycles = int(source_row.get("tile_hbm_cycles") or source_row.get("controller_service_cycles") or 0)
    tile_service_cycles = int(
        source_row.get("replica_recost_tile_service_cycles") or source_row.get("tile_service_cycles") or 1
    )
    controller_cycles = int(service["controller_service_cycles"])
    hbm_excess_cycles = max(0, controller_cycles - max(source_tile_hbm_cycles, tile_service_cycles))
    tile_waves = int(source_row.get("tile_waves", 1) or 1)
    layers = int(source_row.get("layers", 32) or 32)
    clock_ns = float(source_row.get("clock_ns", 1.0) or 1.0)
    added_latency_us = hbm_excess_cycles * tile_waves * layers * clock_ns / 1000.0
    latency_us = source_latency + added_latency_us
    return {
        "source_latency_us": round(source_latency, 6),
        "latency_us": round(latency_us, 6),
        "token_throughput_per_s": round(1_000_000.0 / latency_us, 9) if latency_us > 0.0 else None,
        "source_tile_hbm_cycles": source_tile_hbm_cycles,
        "tile_service_cycles": tile_service_cycles,
        "hbm_excess_cycles_per_wave": hbm_excess_cycles,
        "hbm_added_latency_us": round(added_latency_us, 6),
        "hbm_dominates_tile": controller_cycles > tile_service_cycles,
    }


def _build_row(
    *,
    envelope_row: JsonDict,
    source_row: JsonDict,
    energy_params: JsonDict,
    channel_count: int,
    channel_bw: float,
    burst_bytes: int,
    outstanding: int,
    request_overhead: int,
    row_hit_rate: float,
    row_miss_penalty: int,
    scheduler_efficiency: float,
) -> JsonDict:
    full_tile_bytes = int(source_row.get("onchip_full_tile_bytes", 1048576) or 1048576)
    tile_hbm_bytes = full_tile_bytes * float(envelope_row["hbm_byte_share"])
    service = _hbm_service(
        tile_hbm_bytes=tile_hbm_bytes,
        channel_count=channel_count,
        channel_bandwidth_bytes_per_cycle=channel_bw,
        burst_bytes=burst_bytes,
        outstanding=outstanding,
        request_overhead_cycles=request_overhead,
        row_hit_rate=row_hit_rate,
        row_miss_penalty_cycles=row_miss_penalty,
        scheduler_efficiency=scheduler_efficiency,
    )
    service.update(
        {
            "channel_count": channel_count,
            "channel_bandwidth_bytes_per_cycle": channel_bw,
            "burst_bytes": burst_bytes,
            "hbm_outstanding": outstanding,
            "request_overhead_cycles": request_overhead,
            "row_hit_rate": row_hit_rate,
            "row_miss_penalty_cycles": row_miss_penalty,
            "scheduler_efficiency": scheduler_efficiency,
        }
    )
    latency = _row_latency(source_row=source_row, envelope_row=envelope_row, service=service)
    energy = _hbm_energy(
        tile_hbm_bytes=tile_hbm_bytes,
        service=service,
        params=energy_params,
        source_row=source_row,
    )
    compute_power_mw = float(
        source_row.get("substituted_compute_plus_control_power_mw")
        or source_row.get("substituted_compute_power_mw")
        or source_row.get("replica_recost_compute_power_mw")
        or source_row.get("compute_power_mw")
        or 0.0
    )
    compute_energy_mj = compute_power_mw * float(latency["latency_us"]) * 1.0e-6
    total_energy_mj = compute_energy_mj + float(energy["energy_mj"])
    return {
        "placement_efficiency": envelope_row["placement_efficiency"],
        "shared_sram_capacity_mib": envelope_row["shared_sram_capacity_mib"],
        "hbm_byte_share": envelope_row["hbm_byte_share"],
        "precision_profile": "score32_exp_lut_div",
        "macs_per_cycle": source_row.get("replica_recost_macs_per_cycle") or source_row.get("macs_per_cycle"),
        "hbm_service_model": "channel_burst_row_window_score32_v1",
        **latency,
        "hbm_service": service,
        "hbm_command_calibrated_energy": energy,
        "hbm_energy_mj_per_token": energy["energy_mj"],
        "compute_power_mw": round(compute_power_mw, 6),
        "compute_energy_mj_per_token": round(compute_energy_mj, 9),
        "total_energy_mj_per_token": round(total_energy_mj, 9),
        "remaining_abstractions": [
            "HBM/DRAM service is command/burst/row-hit accounting, not cycle-accurate controller RTL.",
            "HBM energy uses calibrated command-class pJ values, not vendor signoff current traces.",
        ],
    }


def build_report(args: argparse.Namespace) -> JsonDict:
    sram_envelope = _load_json(args.score32_sram_envelope_json)
    measured_command = _load_json(args.score32_measured_command_control_json)
    command_calibrated = _load_json(args.hbm_command_calibrated_service_json)
    source_row = _require_source_score32_row(measured_command)
    energy_params = _calibrated_hbm_energy_params(command_calibrated)
    envelope_rows = list(sram_envelope.get("rows") or [])[: args.frontier_row_limit]
    if not envelope_rows:
        raise ValueError("score32 SRAM envelope contains no rows")
    rows: list[JsonDict] = []
    for envelope_row in envelope_rows:
        for channel_count in args.channel_count:
            for channel_bw in args.channel_bandwidth_bytes_per_cycle:
                for burst_bytes in args.burst_bytes:
                    for outstanding in args.hbm_outstanding:
                        for request_overhead in args.request_overhead_cycles:
                            for row_hit_rate in args.row_hit_rate:
                                for row_miss_penalty in args.row_miss_penalty_cycles:
                                    for scheduler_efficiency in args.scheduler_efficiency:
                                        rows.append(
                                            _build_row(
                                                envelope_row=envelope_row,
                                                source_row=source_row,
                                                energy_params=energy_params,
                                                channel_count=channel_count,
                                                channel_bw=channel_bw,
                                                burst_bytes=burst_bytes,
                                                outstanding=outstanding,
                                                request_overhead=request_overhead,
                                                row_hit_rate=row_hit_rate,
                                                row_miss_penalty=row_miss_penalty,
                                                scheduler_efficiency=scheduler_efficiency,
                                            )
                                        )
    rows_sorted = sorted(rows, key=lambda row: (float(row["latency_us"]), float(row["total_energy_mj_per_token"])))
    best_latency = rows_sorted[0]
    best_energy = min(rows, key=lambda row: (float(row["total_energy_mj_per_token"]), float(row["latency_us"])))
    hbm_dominant_count = sum(1 for row in rows if row["hbm_dominates_tile"])
    decision = (
        "score32_exp_lut_hbm_dram_service_closure_compute_dominant"
        if hbm_dominant_count == 0
        else "score32_exp_lut_hbm_dram_service_closure_hbm_sensitive"
    )
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_exp_lut_hbm_dram_service_closure_v1",
        "decision": decision,
        "inputs": {
            "score32_sram_envelope_json": str(args.score32_sram_envelope_json),
            "score32_measured_command_control_json": str(args.score32_measured_command_control_json),
            "hbm_command_calibrated_service_json": str(args.hbm_command_calibrated_service_json),
        },
        "diagnosis": {
            "best_latency_us": best_latency["latency_us"],
            "best_latency_token_throughput_per_s": best_latency["token_throughput_per_s"],
            "best_latency_hbm_energy_mj_per_token": best_latency["hbm_energy_mj_per_token"],
            "best_latency_compute_energy_mj_per_token": best_latency["compute_energy_mj_per_token"],
            "best_latency_total_energy_mj_per_token": best_latency["total_energy_mj_per_token"],
            "best_energy_us": best_energy["latency_us"],
            "best_energy_token_throughput_per_s": best_energy["token_throughput_per_s"],
            "best_energy_hbm_energy_mj_per_token": best_energy["hbm_energy_mj_per_token"],
            "best_energy_compute_energy_mj_per_token": best_energy["compute_energy_mj_per_token"],
            "best_energy_total_energy_mj_per_token": best_energy["total_energy_mj_per_token"],
            "hbm_dominant_row_count": hbm_dominant_count,
            "row_count": len(rows),
            "source_score32_latency_us": source_row.get("replica_recost_latency_us")
            or source_row.get("adjusted_latency_us_if_feasible"),
            "source_controller_service_cycles": source_row.get("controller_service_cycles")
            or source_row.get("tile_hbm_cycles"),
            "source_tile_service_cycles": source_row.get("replica_recost_tile_service_cycles")
            or source_row.get("tile_service_cycles"),
            "precision_profile": "score32_exp_lut_div",
            "remaining_abstractions": ["cycle_accurate_hbm_controller_rtl", "hbm_vendor_current_signoff"],
        },
        "best_latency": best_latency,
        "best_energy": best_energy,
        "top_rows": rows_sorted[: args.top_k],
        "energy_params": energy_params,
        "assumptions": [
            "The score32 exp-LUT compute/datapath, command control, SRAM envelope, and precision evidence are inherited from merged score32 results.",
            "HBM service is modeled with channel count, per-channel bytes/cycle, burst size, outstanding window, row-hit rate, and scheduler efficiency.",
            "HBM energy uses the existing command-calibrated pJ parameters from the design registry calibration chain.",
            "This is not a cycle-accurate HBM/DRAM controller RTL simulation or vendor current signoff.",
        ],
        "next_step": {
            "requires_cycle_accurate_hbm_controller": True,
            "requires_vendor_hbm_current_signoff": True,
            "recommended_next_step": (
                "Use this score32 HBM/DRAM service closure as the current frontier account; "
                "next close either HBM controller RTL/timing or aggregate full-token energy ranking."
            ),
        },
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diagnosis = payload["diagnosis"]
    best = payload["best_latency"]
    lines = [
        "# Score32 exp-LUT HBM/DRAM Service Closure",
        "",
        f"- decision: `{payload['decision']}`",
        f"- best latency us: `{diagnosis['best_latency_us']}`",
        f"- best throughput token/s: `{diagnosis['best_latency_token_throughput_per_s']}`",
        f"- best latency HBM energy mJ/token: `{diagnosis['best_latency_hbm_energy_mj_per_token']}`",
        f"- best latency total energy mJ/token: `{diagnosis['best_latency_total_energy_mj_per_token']}`",
        f"- HBM-dominant rows: `{diagnosis['hbm_dominant_row_count']}` / `{diagnosis['row_count']}`",
        "",
        "## Best Latency",
        "",
        "| latency us | token/s | HBM energy mJ | total energy mJ | hbm share | efficiency | "
        "channels | ch B/cyc | burst | outstanding | row hit | sched | service cyc |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {latency_us} | {token_throughput_per_s} | {hbm_energy_mj_per_token} | {total_energy_mj_per_token} | {hbm_byte_share} | "
        "{placement_efficiency} | {channel_count} | {channel_bandwidth_bytes_per_cycle} | {burst_bytes} | "
        "{hbm_outstanding} | {row_hit_rate} | {scheduler_efficiency} | {controller_service_cycles} |".format(
            channel_count=best["hbm_service"]["channel_count"],
            channel_bandwidth_bytes_per_cycle=best["hbm_service"]["channel_bandwidth_bytes_per_cycle"],
            burst_bytes=best["hbm_service"]["burst_bytes"],
            hbm_outstanding=best["hbm_service"]["hbm_outstanding"],
            row_hit_rate=best["hbm_service"]["row_hit_rate"],
            scheduler_efficiency=best["hbm_service"]["scheduler_efficiency"],
            controller_service_cycles=best["hbm_service"]["controller_service_cycles"],
            **best,
        ),
        "",
        "## Assumptions",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score32-sram-envelope-json", type=Path, required=True)
    parser.add_argument("--score32-measured-command-control-json", type=Path, required=True)
    parser.add_argument("--hbm-command-calibrated-service-json", type=Path, required=True)
    parser.add_argument("--frontier-row-limit", type=int, default=5)
    parser.add_argument("--channel-count", type=_int_list, default=[4, 8, 16])
    parser.add_argument("--channel-bandwidth-bytes-per-cycle", type=_float_list, default=[256, 512, 1024])
    parser.add_argument("--burst-bytes", type=_int_list, default=[256, 512, 1024])
    parser.add_argument("--hbm-outstanding", type=_int_list, default=[4, 8, 16, 32])
    parser.add_argument("--request-overhead-cycles", type=_int_list, default=[2, 4, 8])
    parser.add_argument("--row-hit-rate", type=_float_list, default=[0.5, 0.75, 0.9])
    parser.add_argument("--row-miss-penalty-cycles", type=_int_list, default=[8, 16, 32])
    parser.add_argument("--scheduler-efficiency", type=_float_list, default=[0.6, 0.75, 0.9])
    parser.add_argument("--top-k", type=int, default=50)
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

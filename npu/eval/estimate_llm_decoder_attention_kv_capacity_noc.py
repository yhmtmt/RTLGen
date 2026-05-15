#!/usr/bin/env python3
"""Estimate capacity-constrained decoder attention/KV memory and NoC choices."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return items


def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items or any(item <= 0.0 for item in items):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return items


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated strings")
    return items


def _ceil_div(a: int | float, b: int | float) -> int:
    return int(math.ceil(a / b)) if a else 0


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _kv_heads(*, attention_heads: int, kv_sharing: str) -> int:
    if kv_sharing == "mha":
        return attention_heads
    if kv_sharing == "gqa4":
        return max(1, math.ceil(attention_heads / 4))
    if kv_sharing == "gqa8":
        return max(1, math.ceil(attention_heads / 8))
    if kv_sharing == "mqa":
        return 1
    raise ValueError(f"unsupported kv sharing: {kv_sharing}")


def _shapes() -> list[JsonDict]:
    return [
        {"label": "gpt2_small", "layers": 12, "hidden_size": 768, "attention_heads": 12},
        {"label": "gpt2_medium_proxy", "layers": 24, "hidden_size": 1024, "attention_heads": 16},
        {"label": "llama7b_proxy", "layers": 32, "hidden_size": 4096, "attention_heads": 32},
    ]


def _sram_capacity_bytes(
    *,
    die_area_mm2: float,
    sram_area_fraction: float,
    usable_sram_fraction: float,
    bitcell_area_um2_per_bit: float,
) -> int:
    sram_area_um2 = die_area_mm2 * 1_000_000.0 * sram_area_fraction * usable_sram_fraction
    return int(sram_area_um2 / bitcell_area_um2_per_bit / 8.0)


def _effective_remote_bw(*, noc_bandwidth_bytes_per_cycle: float, noc_hops: int) -> float:
    return noc_bandwidth_bytes_per_cycle / max(1, noc_hops)


def _placement_rows(
    *,
    shape: JsonDict,
    sequence_length: int,
    kv_sharing: str,
    kv_bits: int,
    die_area_mm2: float,
    sram_area_fraction: float,
    usable_sram_fraction: float,
    bitcell_area_um2_per_bit: float,
    local_sram_fraction: float,
    bank_count: int,
    bank_bandwidth_bytes_per_cycle: float,
    noc_bandwidth_bytes_per_cycle: float,
    noc_hops: int,
    hbm_bandwidth_bytes_per_cycle: float,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> list[JsonDict]:
    layers = int(shape["layers"])
    hidden_size = int(shape["hidden_size"])
    attention_heads = int(shape["attention_heads"])
    head_dim = hidden_size // attention_heads
    kv_heads = _kv_heads(attention_heads=attention_heads, kv_sharing=kv_sharing)
    kv_width = kv_heads * head_dim
    kv_byte_width = _byte_width(kv_bits)
    kv_cache_bytes = 2 * sequence_length * kv_width * kv_byte_width * layers
    kv_read_bytes = kv_cache_bytes
    kv_write_bytes = 2 * kv_width * kv_byte_width * layers

    total_sram_bytes = _sram_capacity_bytes(
        die_area_mm2=die_area_mm2,
        sram_area_fraction=sram_area_fraction,
        usable_sram_fraction=usable_sram_fraction,
        bitcell_area_um2_per_bit=bitcell_area_um2_per_bit,
    )
    local_capacity_bytes = int(total_sram_bytes * local_sram_fraction)
    shared_capacity_bytes = max(0, total_sram_bytes - local_capacity_bytes)
    local_bank_bw = bank_count * bank_bandwidth_bytes_per_cycle
    shared_bank_bw = bank_count * bank_bandwidth_bytes_per_cycle
    remote_bw = _effective_remote_bw(
        noc_bandwidth_bytes_per_cycle=noc_bandwidth_bytes_per_cycle,
        noc_hops=noc_hops,
    )

    qkv_macs = layers * (hidden_size * hidden_size + 2 * hidden_size * kv_width)
    qk_value_macs = layers * (2 * sequence_length * hidden_size)
    softmax_ops = layers * (5 * attention_heads * sequence_length)
    qkv_cycles = _ceil_div(qkv_macs, macs_per_cycle)
    qk_value_compute_cycles = _ceil_div(qk_value_macs, macs_per_cycle)
    softmax_cycles = _ceil_div(softmax_ops, vector_ops_per_cycle)

    base = {
        "label": shape["label"],
        "layers": layers,
        "hidden_size": hidden_size,
        "attention_heads": attention_heads,
        "sequence_length": sequence_length,
        "kv_sharing": kv_sharing,
        "kv_heads": kv_heads,
        "kv_bits": kv_bits,
        "kv_cache_bytes": kv_cache_bytes,
        "kv_cache_mib": round(kv_cache_bytes / (1024 * 1024), 6),
        "kv_cache_sram_area_mm2_at_selected_bitcell": round(
            kv_cache_bytes * 8 * bitcell_area_um2_per_bit / 1_000_000.0,
            6,
        ),
        "die_area_mm2": die_area_mm2,
        "sram_area_fraction": sram_area_fraction,
        "usable_sram_fraction": usable_sram_fraction,
        "bitcell_area_um2_per_bit": bitcell_area_um2_per_bit,
        "total_sram_mib": round(total_sram_bytes / (1024 * 1024), 6),
        "local_sram_fraction": local_sram_fraction,
        "local_capacity_mib": round(local_capacity_bytes / (1024 * 1024), 6),
        "shared_capacity_mib": round(shared_capacity_bytes / (1024 * 1024), 6),
        "bank_count": bank_count,
        "bank_bandwidth_bytes_per_cycle": bank_bandwidth_bytes_per_cycle,
        "noc_bandwidth_bytes_per_cycle": noc_bandwidth_bytes_per_cycle,
        "noc_hops": noc_hops,
        "hbm_bandwidth_bytes_per_cycle": hbm_bandwidth_bytes_per_cycle,
        "macs_per_cycle": macs_per_cycle,
        "vector_ops_per_cycle": vector_ops_per_cycle,
        "qkv_cycles": qkv_cycles,
        "qk_value_compute_cycles": qk_value_compute_cycles,
        "softmax_cycles": softmax_cycles,
    }

    rows: list[JsonDict] = []

    def add_row(
        *,
        placement: str,
        feasible: bool,
        capacity_bytes: int | None,
        local_bytes: int,
        shared_bytes: int,
        hbm_bytes: int,
        kv_access_cycles: int,
        noc_cycles: int,
        limiter: str,
    ) -> None:
        attention_cycles = qkv_cycles + max(qk_value_compute_cycles, kv_access_cycles) + softmax_cycles
        rows.append(
            {
                **base,
                "placement": placement,
                "feasible": feasible,
                "capacity_mib": round((capacity_bytes or 0) / (1024 * 1024), 6),
                "local_bytes": local_bytes,
                "shared_bytes": shared_bytes,
                "hbm_bytes": hbm_bytes,
                "kv_access_cycles": kv_access_cycles,
                "noc_cycles": noc_cycles,
                "attention_cycles": attention_cycles,
                "total_latency_us": round(attention_cycles * clock_ns / 1000.0, 6),
                "limiter": limiter,
                "noc_utilization_proxy": round(noc_cycles / kv_access_cycles, 6) if kv_access_cycles else 0.0,
                "hbm_byte_share": round(hbm_bytes / kv_read_bytes, 6) if kv_read_bytes else 0.0,
            }
        )

    local_feasible = kv_cache_bytes <= local_capacity_bytes
    local_cycles = _ceil_div(kv_read_bytes + kv_write_bytes, local_bank_bw)
    add_row(
        placement="local_sram",
        feasible=local_feasible,
        capacity_bytes=local_capacity_bytes,
        local_bytes=kv_read_bytes,
        shared_bytes=0,
        hbm_bytes=0,
        kv_access_cycles=local_cycles,
        noc_cycles=0,
        limiter="local_bank_bw" if local_feasible and local_cycles >= qk_value_compute_cycles else "compute",
    )

    shared_feasible = kv_cache_bytes <= shared_capacity_bytes
    shared_mem_bw = min(shared_bank_bw, remote_bw)
    shared_cycles = _ceil_div(kv_read_bytes + kv_write_bytes, shared_mem_bw)
    shared_noc_cycles = _ceil_div(kv_read_bytes + kv_write_bytes, remote_bw)
    add_row(
        placement="shared_sram",
        feasible=shared_feasible,
        capacity_bytes=shared_capacity_bytes,
        local_bytes=0,
        shared_bytes=kv_read_bytes,
        hbm_bytes=0,
        kv_access_cycles=shared_cycles,
        noc_cycles=shared_noc_cycles,
        limiter="noc_bw" if remote_bw <= shared_bank_bw else "shared_bank_bw",
    )

    shared_resident = min(kv_cache_bytes, shared_capacity_bytes)
    shared_read_bytes = int(kv_read_bytes * (shared_resident / kv_cache_bytes)) if kv_cache_bytes else 0
    hbm_read_bytes = max(0, kv_read_bytes - shared_read_bytes)
    spill_shared_cycles = _ceil_div(shared_read_bytes + kv_write_bytes, shared_mem_bw) if shared_read_bytes else 0
    spill_hbm_cycles = _ceil_div(hbm_read_bytes, hbm_bandwidth_bytes_per_cycle)
    spill_noc_cycles = _ceil_div(shared_read_bytes + kv_write_bytes, remote_bw) if shared_read_bytes else 0
    add_row(
        placement="shared_sram_hbm_spill",
        feasible=True,
        capacity_bytes=shared_capacity_bytes,
        local_bytes=0,
        shared_bytes=shared_read_bytes,
        hbm_bytes=hbm_read_bytes,
        kv_access_cycles=spill_shared_cycles + spill_hbm_cycles,
        noc_cycles=spill_noc_cycles,
        limiter="hbm_bw" if hbm_read_bytes else ("noc_bw" if remote_bw <= shared_bank_bw else "shared_bank_bw"),
    )

    hbm_cycles = _ceil_div(kv_read_bytes + kv_write_bytes, hbm_bandwidth_bytes_per_cycle)
    add_row(
        placement="hbm",
        feasible=True,
        capacity_bytes=None,
        local_bytes=0,
        shared_bytes=0,
        hbm_bytes=kv_read_bytes,
        kv_access_cycles=hbm_cycles,
        noc_cycles=0,
        limiter="hbm_bw" if hbm_cycles >= qk_value_compute_cycles else "compute",
    )

    return rows


def build_report(
    *,
    sequence_length_list: list[int],
    kv_sharing_list: list[str],
    kv_bits_list: list[int],
    die_area_mm2_list: list[float],
    sram_area_fraction_list: list[float],
    usable_sram_fraction_list: list[float],
    bitcell_area_um2_per_bit_list: list[float],
    local_sram_fraction_list: list[float],
    bank_count_list: list[int],
    bank_bandwidth_bytes_per_cycle_list: list[float],
    noc_bandwidth_bytes_per_cycle_list: list[float],
    noc_hops_list: list[int],
    hbm_bandwidth_bytes_per_cycle_list: list[float],
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> JsonDict:
    all_rows: list[JsonDict] = []
    for shape in _shapes():
        for sequence_length in sequence_length_list:
            for kv_sharing in kv_sharing_list:
                for kv_bits in kv_bits_list:
                    for die_area_mm2 in die_area_mm2_list:
                        for sram_area_fraction in sram_area_fraction_list:
                            for usable_sram_fraction in usable_sram_fraction_list:
                                for bitcell_area in bitcell_area_um2_per_bit_list:
                                    for local_sram_fraction in local_sram_fraction_list:
                                        for bank_count in bank_count_list:
                                            for bank_bw in bank_bandwidth_bytes_per_cycle_list:
                                                for noc_bw in noc_bandwidth_bytes_per_cycle_list:
                                                    for noc_hops in noc_hops_list:
                                                        for hbm_bw in hbm_bandwidth_bytes_per_cycle_list:
                                                            all_rows.extend(
                                                                _placement_rows(
                                                                    shape=shape,
                                                                    sequence_length=sequence_length,
                                                                    kv_sharing=kv_sharing,
                                                                    kv_bits=kv_bits,
                                                                    die_area_mm2=die_area_mm2,
                                                                    sram_area_fraction=sram_area_fraction,
                                                                    usable_sram_fraction=usable_sram_fraction,
                                                                    bitcell_area_um2_per_bit=bitcell_area,
                                                                    local_sram_fraction=local_sram_fraction,
                                                                    bank_count=bank_count,
                                                                    bank_bandwidth_bytes_per_cycle=bank_bw,
                                                                    noc_bandwidth_bytes_per_cycle=noc_bw,
                                                                    noc_hops=noc_hops,
                                                                    hbm_bandwidth_bytes_per_cycle=hbm_bw,
                                                                    macs_per_cycle=macs_per_cycle,
                                                                    vector_ops_per_cycle=vector_ops_per_cycle,
                                                                    clock_ns=clock_ns,
                                                                )
                                                            )

    feasible_rows = [row for row in all_rows if row["feasible"]]
    best_by_die: dict[tuple[str, int, float], JsonDict] = {}
    best_by_shape: dict[tuple[str, int], JsonDict] = {}
    for row in feasible_rows:
        die_key = (str(row["label"]), int(row["sequence_length"]), float(row["die_area_mm2"]))
        shape_key = (str(row["label"]), int(row["sequence_length"]))
        if die_key not in best_by_die or row["total_latency_us"] < best_by_die[die_key]["total_latency_us"]:
            best_by_die[die_key] = row
        if shape_key not in best_by_shape or row["total_latency_us"] < best_by_shape[shape_key]["total_latency_us"]:
            best_by_shape[shape_key] = row

    limiter_counts: dict[str, int] = {}
    placement_counts: dict[str, int] = {}
    for row in best_by_die.values():
        limiter_counts[row["limiter"]] = limiter_counts.get(row["limiter"], 0) + 1
        placement_counts[row["placement"]] = placement_counts.get(row["placement"], 0) + 1

    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_capacity_noc_baseline_v1",
        "inputs": {
            "sequence_length_list": sequence_length_list,
            "kv_sharing_list": kv_sharing_list,
            "kv_bits_list": kv_bits_list,
            "die_area_mm2_list": die_area_mm2_list,
            "sram_area_fraction_list": sram_area_fraction_list,
            "usable_sram_fraction_list": usable_sram_fraction_list,
            "bitcell_area_um2_per_bit_list": bitcell_area_um2_per_bit_list,
            "local_sram_fraction_list": local_sram_fraction_list,
            "bank_count_list": bank_count_list,
            "bank_bandwidth_bytes_per_cycle_list": bank_bandwidth_bytes_per_cycle_list,
            "noc_bandwidth_bytes_per_cycle_list": noc_bandwidth_bytes_per_cycle_list,
            "noc_hops_list": noc_hops_list,
            "hbm_bandwidth_bytes_per_cycle_list": hbm_bandwidth_bytes_per_cycle_list,
            "macs_per_cycle": macs_per_cycle,
            "vector_ops_per_cycle": vector_ops_per_cycle,
            "clock_ns": clock_ns,
        },
        "sweep_summary": {
            "generated_row_count": len(all_rows),
            "feasible_row_count": len(feasible_rows),
            "best_by_die_row_count": len(best_by_die),
            "placement_counts_on_best_by_die": placement_counts,
            "limiter_counts_on_best_by_die": limiter_counts,
        },
        "best_by_die": sorted(
            best_by_die.values(),
            key=lambda row: (row["label"], row["sequence_length"], row["die_area_mm2"]),
        ),
        "best_by_shape": sorted(
            best_by_shape.values(),
            key=lambda row: (row["label"], row["sequence_length"]),
        ),
        "assumptions": [
            "This is a capacity/bandwidth baseline, not a cycle-accurate NoC scheduler.",
            "Local SRAM and shared SRAM placements are disallowed unless the full KV cache fits in the selected capacity.",
            "The shared_sram_hbm_spill placement reads the resident fraction from shared SRAM and the remainder from HBM.",
            "NoC bandwidth is approximated as bisection bandwidth divided by hop count for shared SRAM traffic.",
            "Bank conflicts, packet arbitration, routing, replacement, ECC, and SRAM macro timing are not modeled.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Attention/KV Capacity + NoC Baseline",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- feasible_row_count: `{payload['sweep_summary']['feasible_row_count']}`",
        "",
        "## Best By Die",
        "",
        "| shape | seq | die_mm2 | placement | share | bits | latency_us | kv_MiB | total_sram_MiB | local_MiB | shared_MiB | limiter | noc_hops | noc_B/cyc | bank_count | bank_B/cyc |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in payload["best_by_die"]:
        lines.append(
            "| {label} | {seq} | {die} | {placement} | {share} | {bits} | {lat} | {kv} | {total} | {local} | {shared} | {limiter} | {hops} | {noc} | {banks} | {bank_bw} |".format(
                label=row["label"],
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                placement=row["placement"],
                share=row["kv_sharing"],
                bits=row["kv_bits"],
                lat=row["total_latency_us"],
                kv=row["kv_cache_mib"],
                total=row["total_sram_mib"],
                local=row["local_capacity_mib"],
                shared=row["shared_capacity_mib"],
                limiter=row["limiter"],
                hops=row["noc_hops"],
                noc=row["noc_bandwidth_bytes_per_cycle"],
                banks=row["bank_count"],
                bank_bw=row["bank_bandwidth_bytes_per_cycle"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sequence-length-list", type=_int_list, default=[32768, 131072])
    ap.add_argument("--kv-sharing-list", type=_str_list, default=["mqa", "gqa8", "mha"])
    ap.add_argument("--kv-bits-list", type=_int_list, default=[8, 16])
    ap.add_argument("--die-area-mm2-list", type=_float_list, default=[25, 50, 100, 200, 400])
    ap.add_argument("--sram-area-fraction-list", type=_float_list, default=[0.2, 0.4, 0.6])
    ap.add_argument("--usable-sram-fraction-list", type=_float_list, default=[0.55, 0.7])
    ap.add_argument("--bitcell-area-um2-per-bit-list", type=_float_list, default=[0.02, 0.05, 0.1])
    ap.add_argument("--local-sram-fraction-list", type=_float_list, default=[0.25, 0.5, 0.75])
    ap.add_argument("--bank-count-list", type=_int_list, default=[16, 64, 256])
    ap.add_argument("--bank-bandwidth-bytes-per-cycle-list", type=_float_list, default=[64, 256, 1024])
    ap.add_argument("--noc-bandwidth-bytes-per-cycle-list", type=_float_list, default=[1024, 4096, 16384])
    ap.add_argument("--noc-hops-list", type=_int_list, default=[1, 2, 4, 8])
    ap.add_argument("--hbm-bandwidth-bytes-per-cycle-list", type=_float_list, default=[256, 1024, 4096])
    ap.add_argument("--macs-per-cycle", type=int, default=524288)
    ap.add_argument("--vector-ops-per-cycle", type=int, default=65536)
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        sequence_length_list=args.sequence_length_list,
        kv_sharing_list=args.kv_sharing_list,
        kv_bits_list=args.kv_bits_list,
        die_area_mm2_list=args.die_area_mm2_list,
        sram_area_fraction_list=args.sram_area_fraction_list,
        usable_sram_fraction_list=args.usable_sram_fraction_list,
        bitcell_area_um2_per_bit_list=args.bitcell_area_um2_per_bit_list,
        local_sram_fraction_list=args.local_sram_fraction_list,
        bank_count_list=args.bank_count_list,
        bank_bandwidth_bytes_per_cycle_list=args.bank_bandwidth_bytes_per_cycle_list,
        noc_bandwidth_bytes_per_cycle_list=args.noc_bandwidth_bytes_per_cycle_list,
        noc_hops_list=args.noc_hops_list,
        hbm_bandwidth_bytes_per_cycle_list=args.hbm_bandwidth_bytes_per_cycle_list,
        macs_per_cycle=args.macs_per_cycle,
        vector_ops_per_cycle=args.vector_ops_per_cycle,
        clock_ns=args.clock_ns,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

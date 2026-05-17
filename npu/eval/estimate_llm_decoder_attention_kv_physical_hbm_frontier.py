#!/usr/bin/env python3
"""Estimate llama decoder attention/KV physical HBM and KV-reduction frontier."""

from __future__ import annotations

import argparse
import itertools
import heapq
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


def _sram_capacity_bytes(
    *,
    die_area_mm2: float,
    sram_area_fraction: float,
    usable_sram_fraction: float,
    bitcell_area_um2_per_bit: float,
) -> int:
    area_um2 = die_area_mm2 * 1_000_000.0 * sram_area_fraction * usable_sram_fraction
    return int(area_um2 / bitcell_area_um2_per_bit / 8.0)


def _physical_hbm_bytes_per_cycle(
    *,
    stack_count: int,
    pseudo_channels_per_stack: int,
    pseudo_channel_width_bits: int,
    data_rate_mtps: int,
    core_clock_ns: float,
) -> float:
    transfers_per_core_cycle = data_rate_mtps * core_clock_ns / 1000.0
    bytes_per_pseudo_channel = pseudo_channel_width_bits / 8.0
    return stack_count * pseudo_channels_per_stack * bytes_per_pseudo_channel * transfers_per_core_cycle


def _active_banks(*, tile_tokens: int, bank_interleave_tokens: int, bank_count: int) -> int:
    return max(1, min(bank_count, _ceil_div(tile_tokens, bank_interleave_tokens)))


def _simulate_layer(
    *,
    hidden_size: int,
    attention_heads: int,
    kv_heads: int,
    sequence_length: int,
    kv_bits: int,
    shared_read_share: float,
    hbm_read_share: float,
    tile_tokens: int,
    prefetch_distance_tiles: int,
    hbm_outstanding: int,
    effective_hbm_bytes_per_cycle: float,
    bank_count: int,
    bank_bandwidth_bytes_per_cycle: float,
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    noc_bandwidth_bytes_per_cycle: float,
    noc_hops: int,
    arbitration_efficiency: float,
    virtual_channels: int,
    router_latency_cycles_per_hop: int,
    prefetch_start: str,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
) -> JsonDict:
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    kv_bytes_per_scalar = kv_bits / 8.0
    qkv_macs = hidden_size * hidden_size + 2 * hidden_size * kv_width
    qkv_cycles = _ceil_div(qkv_macs, macs_per_cycle)
    tile_count = _ceil_div(sequence_length, tile_tokens)
    active_banks = _active_banks(
        tile_tokens=tile_tokens,
        bank_interleave_tokens=bank_interleave_tokens,
        bank_count=bank_count,
    )
    shared_bank_bw = active_banks * bank_bandwidth_bytes_per_cycle * bank_conflict_efficiency
    vc_gain = min(1.0, 0.85 + 0.05 * max(0, virtual_channels - 1))
    noc_eff_bw = (noc_bandwidth_bytes_per_cycle / max(1, noc_hops)) * arbitration_efficiency * vc_gain

    tile_compute_cycles = _ceil_div(2 * tile_tokens * hidden_size, macs_per_cycle)
    tile_softmax_cycles = _ceil_div(5 * attention_heads * tile_tokens, vector_ops_per_cycle)
    tile_attention_cycles = tile_compute_cycles + tile_softmax_cycles
    full_tile_bytes = 2 * tile_tokens * kv_width * kv_bytes_per_scalar
    full_shared_bytes = full_tile_bytes * shared_read_share
    full_hbm_bytes = full_tile_bytes * hbm_read_share
    tile_shared_bank_cycles = _ceil_div(full_shared_bytes, shared_bank_bw)
    tile_noc_cycles = _ceil_div(full_shared_bytes, noc_eff_bw) + noc_hops * router_latency_cycles_per_hop
    tile_shared_path_cycles = max(tile_shared_bank_cycles, tile_noc_cycles)
    tile_hbm_cycles = _ceil_div(full_hbm_bytes, effective_hbm_bytes_per_cycle)

    earliest_hbm_start = 0 if prefetch_start == "during_qkv" else qkv_cycles
    hbm_lane_heap = [0 for _ in range(max(1, hbm_outstanding))]
    heapq.heapify(hbm_lane_heap)
    shared_done: list[int] = []
    shared_free = qkv_cycles
    compute_done: list[int] = []
    compute_free = qkv_cycles
    hbm_stall_cycles = 0
    shared_stall_cycles = 0
    compute_wait_cycles = 0
    prefetch_stall_cycles = 0
    for tile_index in range(tile_count):
        window_release = earliest_hbm_start
        if tile_index > prefetch_distance_tiles:
            window_source = tile_index - prefetch_distance_tiles - 1
            window_release = max(window_release, compute_done[window_source])
        hbm_lane_free = heapq.heappop(hbm_lane_heap)
        hbm_start = max(hbm_lane_free, window_release)
        prefetch_stall_cycles += max(0, hbm_start - hbm_lane_free)
        hbm_finish = hbm_start + tile_hbm_cycles
        heapq.heappush(hbm_lane_heap, hbm_finish)

        shared_start = shared_free
        shared_finish = shared_start + tile_shared_path_cycles
        shared_done.append(shared_finish)
        shared_free = shared_finish

        ready = max(hbm_finish, shared_finish, qkv_cycles)
        compute_start = max(compute_free, ready)
        hbm_stall_cycles += max(0, hbm_finish - compute_free)
        shared_stall_cycles += max(0, shared_finish - compute_free)
        compute_wait_cycles += max(0, compute_start - compute_free)
        compute_free = compute_start + tile_attention_cycles
        compute_done.append(compute_free)

    kv_write_bytes = 2 * kv_width * kv_bytes_per_scalar
    kv_write_shared_cycles = _ceil_div(kv_write_bytes, min(shared_bank_bw, noc_eff_bw))
    layer_cycles = compute_free + kv_write_shared_cycles
    dominant = max(
        {
            "tile_attention": tile_attention_cycles,
            "shared_path": tile_shared_path_cycles,
            "hbm": tile_hbm_cycles,
        }.items(),
        key=lambda item: item[1],
    )[0]
    return {
        "tile_count": tile_count,
        "active_banks": active_banks,
        "qkv_cycles": qkv_cycles,
        "tile_attention_cycles": tile_attention_cycles,
        "tile_shared_path_cycles": tile_shared_path_cycles,
        "tile_hbm_cycles": tile_hbm_cycles,
        "kv_write_shared_cycles": kv_write_shared_cycles,
        "layer_cycles": layer_cycles,
        "hbm_stall_cycles": hbm_stall_cycles,
        "shared_stall_cycles": shared_stall_cycles,
        "compute_wait_cycles": compute_wait_cycles,
        "prefetch_stall_cycles": prefetch_stall_cycles,
        "noc_effective_bytes_per_cycle": round(noc_eff_bw, 6),
        "dominant_tile_resource": dominant,
    }


def _shape_row(
    *,
    label: str,
    layers: int,
    hidden_size: int,
    attention_heads: int,
    sequence_length: int,
    kv_sharing: str,
    kv_bits: int,
    die_area_mm2: float,
    sram_area_fraction: float,
    usable_sram_fraction: float,
    bitcell_area_um2_per_bit: float,
    local_sram_fraction: float,
    stack_count: int,
    pseudo_channels_per_stack: int,
    pseudo_channel_width_bits: int,
    data_rate_mtps: int,
    hbm_efficiency: float,
    tile_tokens: int,
    prefetch_distance_tiles: int,
    hbm_outstanding: int,
    arbitration_efficiency: float,
    virtual_channels: int,
    prefetch_start: str,
    bank_count: int,
    bank_bandwidth_bytes_per_cycle: float,
    bank_interleave_tokens: int,
    bank_conflict_efficiency: float,
    noc_bandwidth_bytes_per_cycle: float,
    noc_hops: int,
    router_latency_cycles_per_hop: int,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> JsonDict:
    head_dim = hidden_size // attention_heads
    kv_heads = _kv_heads(attention_heads=attention_heads, kv_sharing=kv_sharing)
    kv_width = kv_heads * head_dim
    kv_bytes_per_scalar = kv_bits / 8.0
    kv_cache_bytes = 2 * sequence_length * kv_width * kv_bytes_per_scalar * layers
    total_sram_bytes = _sram_capacity_bytes(
        die_area_mm2=die_area_mm2,
        sram_area_fraction=sram_area_fraction,
        usable_sram_fraction=usable_sram_fraction,
        bitcell_area_um2_per_bit=bitcell_area_um2_per_bit,
    )
    local_capacity_bytes = int(total_sram_bytes * local_sram_fraction)
    shared_capacity_bytes = max(0, total_sram_bytes - local_capacity_bytes)
    shared_resident_bytes = min(kv_cache_bytes, shared_capacity_bytes)
    shared_read_share = shared_resident_bytes / kv_cache_bytes if kv_cache_bytes else 0.0
    hbm_read_share = 1.0 - shared_read_share
    raw_hbm_bw = _physical_hbm_bytes_per_cycle(
        stack_count=stack_count,
        pseudo_channels_per_stack=pseudo_channels_per_stack,
        pseudo_channel_width_bits=pseudo_channel_width_bits,
        data_rate_mtps=data_rate_mtps,
        core_clock_ns=clock_ns,
    )
    effective_hbm_bw = raw_hbm_bw * hbm_efficiency
    layer = _simulate_layer(
        hidden_size=hidden_size,
        attention_heads=attention_heads,
        kv_heads=kv_heads,
        sequence_length=sequence_length,
        kv_bits=kv_bits,
        shared_read_share=shared_read_share,
        hbm_read_share=hbm_read_share,
        tile_tokens=tile_tokens,
        prefetch_distance_tiles=prefetch_distance_tiles,
        hbm_outstanding=hbm_outstanding,
        effective_hbm_bytes_per_cycle=effective_hbm_bw,
        bank_count=bank_count,
        bank_bandwidth_bytes_per_cycle=bank_bandwidth_bytes_per_cycle,
        bank_interleave_tokens=bank_interleave_tokens,
        bank_conflict_efficiency=bank_conflict_efficiency,
        noc_bandwidth_bytes_per_cycle=noc_bandwidth_bytes_per_cycle,
        noc_hops=noc_hops,
        arbitration_efficiency=arbitration_efficiency,
        virtual_channels=virtual_channels,
        router_latency_cycles_per_hop=router_latency_cycles_per_hop,
        prefetch_start=prefetch_start,
        macs_per_cycle=macs_per_cycle,
        vector_ops_per_cycle=vector_ops_per_cycle,
    )
    total_cycles = layer["layer_cycles"] * layers
    return {
        "label": label,
        "layers": layers,
        "hidden_size": hidden_size,
        "attention_heads": attention_heads,
        "sequence_length": sequence_length,
        "die_area_mm2": die_area_mm2,
        "kv_sharing": kv_sharing,
        "kv_heads": kv_heads,
        "kv_bits": kv_bits,
        "kv_cache_mib": round(kv_cache_bytes / (1024 * 1024), 6),
        "sram_area_fraction": sram_area_fraction,
        "usable_sram_fraction": usable_sram_fraction,
        "bitcell_area_um2_per_bit": bitcell_area_um2_per_bit,
        "local_sram_fraction": local_sram_fraction,
        "total_sram_mib": round(total_sram_bytes / (1024 * 1024), 6),
        "shared_capacity_mib": round(shared_capacity_bytes / (1024 * 1024), 6),
        "hbm_byte_share": round(hbm_read_share, 6),
        "bank_count": bank_count,
        "bank_bandwidth_bytes_per_cycle": bank_bandwidth_bytes_per_cycle,
        "bank_interleave_tokens": bank_interleave_tokens,
        "bank_conflict_efficiency": bank_conflict_efficiency,
        "noc_bandwidth_bytes_per_cycle": noc_bandwidth_bytes_per_cycle,
        "noc_hops": noc_hops,
        "router_latency_cycles_per_hop": router_latency_cycles_per_hop,
        "stack_count": stack_count,
        "pseudo_channels_per_stack": pseudo_channels_per_stack,
        "pseudo_channel_width_bits": pseudo_channel_width_bits,
        "data_rate_mtps": data_rate_mtps,
        "raw_hbm_bytes_per_cycle": round(raw_hbm_bw, 6),
        "hbm_efficiency": hbm_efficiency,
        "effective_hbm_bytes_per_cycle": round(effective_hbm_bw, 6),
        "tile_tokens": tile_tokens,
        "prefetch_distance_tiles": prefetch_distance_tiles,
        "hbm_outstanding": hbm_outstanding,
        "arbitration_efficiency": arbitration_efficiency,
        "virtual_channels": virtual_channels,
        "prefetch_start": prefetch_start,
        "macs_per_cycle": macs_per_cycle,
        "vector_ops_per_cycle": vector_ops_per_cycle,
        "clock_ns": clock_ns,
        "total_cycles": total_cycles,
        "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
        **layer,
    }


def _best_by(rows: list[JsonDict], keys: tuple[str, ...]) -> list[JsonDict]:
    best: dict[tuple[Any, ...], JsonDict] = {}
    for row in rows:
        key = tuple(row[name] for name in keys)
        current = best.get(key)
        if current is None or row["latency_us"] < current["latency_us"]:
            best[key] = row
    return sorted(best.values(), key=lambda row: tuple(row[name] for name in keys) + (row["latency_us"],))


def build_report(
    *,
    label: str,
    sequence_length_list: list[int],
    die_area_mm2_list: list[float],
    kv_sharing_list: list[str],
    kv_bits_list: list[int],
    stack_count_list: list[int],
    pseudo_channels_per_stack_list: list[int],
    pseudo_channel_width_bits_list: list[int],
    data_rate_mtps_list: list[int],
    hbm_efficiency_list: list[float],
    tile_tokens_list: list[int],
    prefetch_distance_tiles_list: list[int],
    hbm_outstanding_list: list[int],
    arbitration_efficiency_list: list[float],
    virtual_channel_list: list[int],
    prefetch_start_list: list[str],
    sram_area_fraction_list: list[float],
    usable_sram_fraction_list: list[float],
    bitcell_area_um2_per_bit_list: list[float],
    local_sram_fraction_list: list[float],
    bank_count_list: list[int],
    bank_bandwidth_bytes_per_cycle_list: list[float],
    bank_interleave_tokens_list: list[int],
    bank_conflict_efficiency_list: list[float],
    noc_bandwidth_bytes_per_cycle_list: list[float],
    noc_hops_list: list[int],
    router_latency_cycles_per_hop_list: list[int],
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    clock_ns: float,
) -> JsonDict:
    shapes = {
        "llama7b_proxy": {"layers": 32, "hidden_size": 4096, "attention_heads": 32},
    }
    if label not in shapes:
        raise ValueError(f"unsupported label: {label}")
    shape = shapes[label]
    rows: list[JsonDict] = []
    sweep_axes = (
        sequence_length_list,
        die_area_mm2_list,
        kv_sharing_list,
        kv_bits_list,
        stack_count_list,
        pseudo_channels_per_stack_list,
        pseudo_channel_width_bits_list,
        data_rate_mtps_list,
        hbm_efficiency_list,
        tile_tokens_list,
        prefetch_distance_tiles_list,
        hbm_outstanding_list,
        arbitration_efficiency_list,
        virtual_channel_list,
        prefetch_start_list,
        sram_area_fraction_list,
        usable_sram_fraction_list,
        bitcell_area_um2_per_bit_list,
        local_sram_fraction_list,
        bank_count_list,
        bank_bandwidth_bytes_per_cycle_list,
        bank_interleave_tokens_list,
        bank_conflict_efficiency_list,
        noc_bandwidth_bytes_per_cycle_list,
        noc_hops_list,
        router_latency_cycles_per_hop_list,
    )
    for (
        sequence_length,
        die_area_mm2,
        kv_sharing,
        kv_bits,
        stack_count,
        pseudo_channels_per_stack,
        pseudo_channel_width_bits,
        data_rate_mtps,
        hbm_efficiency,
        tile_tokens,
        prefetch_distance_tiles,
        hbm_outstanding,
        arbitration_efficiency,
        virtual_channels,
        prefetch_start,
        sram_area_fraction,
        usable_sram_fraction,
        bitcell_area_um2_per_bit,
        local_sram_fraction,
        bank_count,
        bank_bandwidth_bytes_per_cycle,
        bank_interleave_tokens,
        bank_conflict_efficiency,
        noc_bandwidth_bytes_per_cycle,
        noc_hops,
        router_latency_cycles_per_hop,
    ) in itertools.product(*sweep_axes):
        rows.append(
            _shape_row(
                label=label,
                sequence_length=sequence_length,
                die_area_mm2=die_area_mm2,
                kv_sharing=kv_sharing,
                kv_bits=kv_bits,
                stack_count=stack_count,
                pseudo_channels_per_stack=pseudo_channels_per_stack,
                pseudo_channel_width_bits=pseudo_channel_width_bits,
                data_rate_mtps=data_rate_mtps,
                hbm_efficiency=hbm_efficiency,
                tile_tokens=tile_tokens,
                prefetch_distance_tiles=prefetch_distance_tiles,
                hbm_outstanding=hbm_outstanding,
                arbitration_efficiency=arbitration_efficiency,
                virtual_channels=virtual_channels,
                prefetch_start=prefetch_start,
                sram_area_fraction=sram_area_fraction,
                usable_sram_fraction=usable_sram_fraction,
                bitcell_area_um2_per_bit=bitcell_area_um2_per_bit,
                local_sram_fraction=local_sram_fraction,
                bank_count=bank_count,
                bank_bandwidth_bytes_per_cycle=bank_bandwidth_bytes_per_cycle,
                bank_interleave_tokens=bank_interleave_tokens,
                bank_conflict_efficiency=bank_conflict_efficiency,
                noc_bandwidth_bytes_per_cycle=noc_bandwidth_bytes_per_cycle,
                noc_hops=noc_hops,
                router_latency_cycles_per_hop=router_latency_cycles_per_hop,
                macs_per_cycle=macs_per_cycle,
                vector_ops_per_cycle=vector_ops_per_cycle,
                clock_ns=clock_ns,
                **shape,
            )
        )

    rows_sorted = sorted(rows, key=lambda row: row["latency_us"])
    dominance: dict[str, int] = {}
    for row in rows:
        key = str(row["dominant_tile_resource"])
        dominance[key] = dominance.get(key, 0) + 1
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_physical_hbm_frontier_llama7b_v1",
        "inputs": {
            "label": label,
            "sequence_length_list": sequence_length_list,
            "die_area_mm2_list": die_area_mm2_list,
            "kv_sharing_list": kv_sharing_list,
            "kv_bits_list": kv_bits_list,
            "stack_count_list": stack_count_list,
            "pseudo_channels_per_stack_list": pseudo_channels_per_stack_list,
            "pseudo_channel_width_bits_list": pseudo_channel_width_bits_list,
            "data_rate_mtps_list": data_rate_mtps_list,
            "hbm_efficiency_list": hbm_efficiency_list,
            "tile_tokens_list": tile_tokens_list,
            "prefetch_distance_tiles_list": prefetch_distance_tiles_list,
            "hbm_outstanding_list": hbm_outstanding_list,
            "sram_area_fraction_list": sram_area_fraction_list,
            "usable_sram_fraction_list": usable_sram_fraction_list,
            "bitcell_area_um2_per_bit_list": bitcell_area_um2_per_bit_list,
            "local_sram_fraction_list": local_sram_fraction_list,
            "bank_count_list": bank_count_list,
            "bank_bandwidth_bytes_per_cycle_list": bank_bandwidth_bytes_per_cycle_list,
            "bank_interleave_tokens_list": bank_interleave_tokens_list,
            "bank_conflict_efficiency_list": bank_conflict_efficiency_list,
            "noc_bandwidth_bytes_per_cycle_list": noc_bandwidth_bytes_per_cycle_list,
            "noc_hops_list": noc_hops_list,
            "router_latency_cycles_per_hop_list": router_latency_cycles_per_hop_list,
            "clock_ns": clock_ns,
        },
        "sweep_summary": {
            "generated_row_count": len(rows),
            "retained_top_row_count": min(50, len(rows_sorted)),
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
        },
        "best": rows_sorted[0],
        "top_rows": rows_sorted[:50],
        "best_by_sequence_die": _best_by(rows, ("sequence_length", "die_area_mm2")),
        "best_by_kv_structure": _best_by(rows, ("sequence_length", "die_area_mm2", "kv_sharing", "kv_bits")),
        "best_by_hbm_physical": _best_by(
            rows,
            (
                "sequence_length",
                "die_area_mm2",
                "stack_count",
                "pseudo_channels_per_stack",
                "pseudo_channel_width_bits",
                "data_rate_mtps",
            ),
        ),
        "best_by_memory_noc": _best_by(
            rows,
            (
                "sequence_length",
                "die_area_mm2",
                "sram_area_fraction",
                "usable_sram_fraction",
                "bitcell_area_um2_per_bit",
                "local_sram_fraction",
                "bank_count",
                "bank_bandwidth_bytes_per_cycle",
                "noc_bandwidth_bytes_per_cycle",
                "noc_hops",
            ),
        ),
        "assumptions": [
            "This is a planning model for single-token decode attention/KV, not a JEDEC HBM timing model.",
            "HBM bandwidth is derived from stack count, pseudo-channel count, interface width, MT/s, and the core clock period.",
            "HBM efficiency represents controller scheduling, protocol overhead, row locality, and clock-crossing loss in aggregate.",
            "KV bits are treated as packed storage bits, so kv4 has half the byte traffic of kv8.",
            "Shared SRAM residency is capacity-based; the remaining KV-cache traffic spills to HBM.",
            "The tile scheduler is a compact service model intended to rank architecture directions before RTL.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Decoder Attention/KV Physical HBM Frontier",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- selected_point: `{best['label']} seq={best['sequence_length']} die={best['die_area_mm2']}mm2`",
        "",
        "## Best",
        "",
        "| seq | die | kv | bits | stacks | pch/stack | width | MT/s | eff | hbm_B/cyc | hbm_share | latency_us | resource |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        "| {seq} | {die} | {kv} | {bits} | {stacks} | {pch} | {width} | {mtps} | {eff} | {bw} | {share} | {lat} | {res} |".format(
            seq=best["sequence_length"],
            die=best["die_area_mm2"],
            kv=best["kv_sharing"],
            bits=best["kv_bits"],
            stacks=best["stack_count"],
            pch=best["pseudo_channels_per_stack"],
            width=best["pseudo_channel_width_bits"],
            mtps=best["data_rate_mtps"],
            eff=best["hbm_efficiency"],
            bw=best["effective_hbm_bytes_per_cycle"],
            share=best["hbm_byte_share"],
            lat=best["latency_us"],
            res=best["dominant_tile_resource"],
        ),
        "",
        "## Best By Sequence And Die",
        "",
        "| seq | die | kv | bits | stacks | MT/s | SRAM MiB | local_frac | NoC B/cyc | hops | hbm_share | latency_us | resource |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["best_by_sequence_die"]:
        lines.append(
            "| {seq} | {die} | {kv} | {bits} | {stacks} | {mtps} | {sram} | {local} | {noc} | {hops} | {share} | {lat} | {res} |".format(
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                kv=row["kv_sharing"],
                bits=row["kv_bits"],
                stacks=row["stack_count"],
                mtps=row["data_rate_mtps"],
                sram=row["total_sram_mib"],
                local=row["local_sram_fraction"],
                noc=row["noc_bandwidth_bytes_per_cycle"],
                hops=row["noc_hops"],
                share=row["hbm_byte_share"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend(
        [
            "",
            "## Top 10",
            "",
            "| rank | seq | die | kv | bits | stacks | pch/stack | MT/s | hbm_B/cyc | hbm_share | latency_us | resource |",
            "|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for index, row in enumerate(payload["top_rows"][:10], start=1):
        lines.append(
            "| {rank} | {seq} | {die} | {kv} | {bits} | {stacks} | {pch} | {mtps} | {bw} | {share} | {lat} | {res} |".format(
                rank=index,
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                kv=row["kv_sharing"],
                bits=row["kv_bits"],
                stacks=row["stack_count"],
                pch=row["pseudo_channels_per_stack"],
                mtps=row["data_rate_mtps"],
                bw=row["effective_hbm_bytes_per_cycle"],
                share=row["hbm_byte_share"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", default="llama7b_proxy")
    ap.add_argument("--sequence-length-list", type=_int_list, default=[32768, 65536, 131072])
    ap.add_argument("--die-area-mm2-list", type=_float_list, default=[100, 200, 400])
    ap.add_argument("--kv-sharing-list", type=_str_list, default=["mha", "gqa4", "gqa8", "mqa"])
    ap.add_argument("--kv-bits-list", type=_int_list, default=[16, 8, 4])
    ap.add_argument("--stack-count-list", type=_int_list, default=[1, 2, 4, 8])
    ap.add_argument("--pseudo-channels-per-stack-list", type=_int_list, default=[8, 16])
    ap.add_argument("--pseudo-channel-width-bits-list", type=_int_list, default=[64])
    ap.add_argument("--data-rate-mtps-list", type=_int_list, default=[3200, 6400, 9000])
    ap.add_argument("--hbm-efficiency-list", type=_float_list, default=[0.35, 0.55, 0.75])
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[512, 1024])
    ap.add_argument("--prefetch-distance-tiles-list", type=_int_list, default=[4])
    ap.add_argument("--hbm-outstanding-list", type=_int_list, default=[8, 16])
    ap.add_argument("--arbitration-efficiency-list", type=_float_list, default=[0.85])
    ap.add_argument("--virtual-channel-list", type=_int_list, default=[4])
    ap.add_argument("--prefetch-start-list", type=_str_list, default=["during_qkv"])
    ap.add_argument("--sram-area-fraction", type=_float_list, default=[0.6])
    ap.add_argument("--usable-sram-fraction", type=_float_list, default=[0.7])
    ap.add_argument("--bitcell-area-um2-per-bit", type=_float_list, default=[0.02])
    ap.add_argument("--local-sram-fraction", type=_float_list, default=[0.25])
    ap.add_argument("--bank-count", type=_int_list, default=[16])
    ap.add_argument("--bank-bandwidth-bytes-per-cycle", type=_float_list, default=[1024.0])
    ap.add_argument("--bank-interleave-tokens", type=_int_list, default=[16])
    ap.add_argument("--bank-conflict-efficiency", type=_float_list, default=[0.75])
    ap.add_argument("--noc-bandwidth-bytes-per-cycle", type=_float_list, default=[16384.0])
    ap.add_argument("--noc-hops", type=_int_list, default=[1])
    ap.add_argument("--router-latency-cycles-per-hop", type=_int_list, default=[2])
    ap.add_argument("--macs-per-cycle", type=int, default=524288)
    ap.add_argument("--vector-ops-per-cycle", type=int, default=65536)
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        label=args.label,
        sequence_length_list=args.sequence_length_list,
        die_area_mm2_list=args.die_area_mm2_list,
        kv_sharing_list=args.kv_sharing_list,
        kv_bits_list=args.kv_bits_list,
        stack_count_list=args.stack_count_list,
        pseudo_channels_per_stack_list=args.pseudo_channels_per_stack_list,
        pseudo_channel_width_bits_list=args.pseudo_channel_width_bits_list,
        data_rate_mtps_list=args.data_rate_mtps_list,
        hbm_efficiency_list=args.hbm_efficiency_list,
        tile_tokens_list=args.tile_tokens_list,
        prefetch_distance_tiles_list=args.prefetch_distance_tiles_list,
        hbm_outstanding_list=args.hbm_outstanding_list,
        arbitration_efficiency_list=args.arbitration_efficiency_list,
        virtual_channel_list=args.virtual_channel_list,
        prefetch_start_list=args.prefetch_start_list,
        sram_area_fraction_list=args.sram_area_fraction,
        usable_sram_fraction_list=args.usable_sram_fraction,
        bitcell_area_um2_per_bit_list=args.bitcell_area_um2_per_bit,
        local_sram_fraction_list=args.local_sram_fraction,
        bank_count_list=args.bank_count,
        bank_bandwidth_bytes_per_cycle_list=args.bank_bandwidth_bytes_per_cycle,
        bank_interleave_tokens_list=args.bank_interleave_tokens,
        bank_conflict_efficiency_list=args.bank_conflict_efficiency,
        noc_bandwidth_bytes_per_cycle_list=args.noc_bandwidth_bytes_per_cycle,
        noc_hops_list=args.noc_hops,
        router_latency_cycles_per_hop_list=args.router_latency_cycles_per_hop,
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

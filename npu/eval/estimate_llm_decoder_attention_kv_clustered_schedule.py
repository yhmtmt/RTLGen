#!/usr/bin/env python3
"""Estimate clustered Llama7B attention scheduling with explicit reductions."""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.estimate_llm_decoder_attention_kv_measured_compute import (  # noqa: E402
    _float_list,
    _int_list,
    _load_compute_candidates,
)
from npu.eval.estimate_llm_decoder_attention_kv_physical_hbm_frontier import (  # noqa: E402
    _active_banks,
    _ceil_div,
    _kv_heads,
    _physical_hbm_bytes_per_cycle,
    _sram_capacity_bytes,
)

JsonDict = dict[str, Any]


def _profile_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _metric(profile: JsonDict, component: str, key: str, default: float = 0.0) -> float:
    raw = profile.get(component, {})
    if not isinstance(raw, dict):
        return default
    value = raw.get(key, default)
    return float(value)


def _path_metric(profile: JsonDict, component: str) -> str:
    raw = profile.get(component, {})
    if not isinstance(raw, dict):
        return ""
    return str(raw.get("metrics_csv", ""))


def _measured_l1_overhead(profile: JsonDict | None, cluster_count: int) -> JsonDict:
    if profile is None:
        return {
            "profile": "analytic_unmeasured",
            "area_um2": 0.0,
            "power_mw": 0.0,
            "clock_ns": 0.0,
            "local_datapath_area_um2": 0.0,
            "local_datapath_power_mw": 0.0,
            "local_datapath_clock_ns": 0.0,
            "noc_fifo_area_um2": 0.0,
            "noc_fifo_power_mw": 0.0,
            "noc_fifo_clock_ns": 0.0,
            "noc_router_area_um2": 0.0,
            "noc_router_power_mw": 0.0,
            "noc_router_clock_ns": 0.0,
            "softmax_weight_generator_area_um2": 0.0,
            "softmax_weight_generator_power_mw": 0.0,
            "softmax_weight_generator_clock_ns": 0.0,
            "fifo_per_cluster": 0,
            "router_per_cluster": 0,
            "softmax_weight_generator_per_cluster": 0,
            "local_datapath_metrics_csv": "",
            "noc_fifo_metrics_csv": "",
            "noc_router_metrics_csv": "",
            "softmax_weight_generator_metrics_csv": "",
        }
    fifo_per_cluster = int(profile.get("fifo_per_cluster", 1))
    router_per_cluster = int(profile.get("router_per_cluster", 1))
    softmax_per_cluster = int(profile.get("softmax_weight_generator_per_cluster", 0))
    local_area = _metric(profile, "local_datapath", "area_um2")
    local_power = _metric(profile, "local_datapath", "power_mw")
    local_clock = _metric(profile, "local_datapath", "clock_ns")
    fifo_area = _metric(profile, "noc_fifo", "area_um2")
    fifo_power = _metric(profile, "noc_fifo", "power_mw")
    fifo_clock = _metric(profile, "noc_fifo", "clock_ns")
    router_area = _metric(profile, "noc_router", "area_um2")
    router_power = _metric(profile, "noc_router", "power_mw")
    router_clock = _metric(profile, "noc_router", "clock_ns")
    softmax_area = _metric(profile, "softmax_weight_generator", "area_um2")
    softmax_power = _metric(profile, "softmax_weight_generator", "power_mw")
    softmax_clock = _metric(profile, "softmax_weight_generator", "clock_ns")
    per_cluster_area = (
        local_area
        + fifo_per_cluster * fifo_area
        + router_per_cluster * router_area
        + softmax_per_cluster * softmax_area
    )
    per_cluster_power = (
        local_power
        + fifo_per_cluster * fifo_power
        + router_per_cluster * router_power
        + softmax_per_cluster * softmax_power
    )
    return {
        "profile": str(profile["name"]),
        "area_um2": cluster_count * per_cluster_area,
        "power_mw": cluster_count * per_cluster_power,
        "clock_ns": max(local_clock, fifo_clock, router_clock, softmax_clock),
        "local_datapath_area_um2": local_area,
        "local_datapath_power_mw": local_power,
        "local_datapath_clock_ns": local_clock,
        "noc_fifo_area_um2": fifo_area,
        "noc_fifo_power_mw": fifo_power,
        "noc_fifo_clock_ns": fifo_clock,
        "noc_router_area_um2": router_area,
        "noc_router_power_mw": router_power,
        "noc_router_clock_ns": router_clock,
        "softmax_weight_generator_area_um2": softmax_area,
        "softmax_weight_generator_power_mw": softmax_power,
        "softmax_weight_generator_clock_ns": softmax_clock,
        "fifo_per_cluster": fifo_per_cluster,
        "router_per_cluster": router_per_cluster,
        "softmax_weight_generator_per_cluster": softmax_per_cluster,
        "local_datapath_metrics_csv": _path_metric(profile, "local_datapath"),
        "noc_fifo_metrics_csv": _path_metric(profile, "noc_fifo"),
        "noc_router_metrics_csv": _path_metric(profile, "noc_router"),
        "softmax_weight_generator_metrics_csv": _path_metric(profile, "softmax_weight_generator"),
    }


def _load_measured_l1_profiles(
    *,
    repo_root: Path,
    costs_path: Path | None,
    profile_names: list[str] | None,
) -> list[JsonDict | None]:
    if costs_path is None:
        return [None]
    resolved = costs_path if costs_path.is_absolute() else repo_root / costs_path
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    raw_profiles = payload.get("profiles", [])
    if isinstance(raw_profiles, dict):
        profiles = list(raw_profiles.values())
    elif isinstance(raw_profiles, list):
        profiles = raw_profiles
    else:
        raise ValueError(f"measured L1 cost profile file has invalid profiles field: {resolved}")
    names = set(profile_names or [])
    if "all" in names:
        names = set()
    selected: list[JsonDict | None] = []
    for profile in profiles:
        if not isinstance(profile, dict) or not profile.get("name"):
            raise ValueError(f"measured L1 cost profile lacks a name: {resolved}")
        if names and str(profile["name"]) not in names:
            continue
        selected.append(profile)
    if not selected:
        raise ValueError(f"no measured L1 cost profiles selected from {resolved}")
    return selected


def _update_best_by(best: dict[tuple[Any, ...], JsonDict], keys: tuple[str, ...], row: JsonDict) -> None:
    key = tuple(row[name] for name in keys)
    current = best.get(key)
    if current is None or row["latency_us"] < current["latency_us"]:
        best[key] = row


def _best_by_values(best: dict[tuple[Any, ...], JsonDict], keys: tuple[str, ...]) -> list[JsonDict]:
    return sorted(best.values(), key=lambda row: tuple(row[name] for name in keys) + (row["latency_us"],))


def _reduction_factor(strategy: str, active_clusters: int) -> tuple[int, int]:
    if strategy == "centralized_tile":
        return 0, active_clusters
    if strategy == "owner_cluster":
        return max(0, active_clusters - 1), max(1, active_clusters)
    if strategy == "cluster_tree":
        return max(0, _ceil_div(math.log2(max(1, active_clusters)), 1)), max(1, active_clusters)
    raise ValueError(f"unsupported reduction strategy: {strategy}")


def _shape_row(
    *,
    candidate: JsonDict,
    die_area_mm2: float,
    sram_area_fraction: float,
    logic_area_fraction: float,
    reserved_area_fraction: float,
    sequence_length: int,
    usable_sram_fraction: float,
    local_sram_fraction: float,
    tile_tokens: int,
    bank_count: int,
    cluster_count: int,
    noc_bandwidth_bytes_per_cycle: float,
    noc_hops: int,
    reduction_strategy: str,
    vector_ops_per_mac: float,
    reduction_scalar_bytes: int,
    command_cycles_per_tile: int,
    command_cycles_per_wave: int,
    reducer_setup_cycles: int,
    reduction_cycle_multiplier: float,
    measured_l1_profile: JsonDict | None,
) -> JsonDict | None:
    if sram_area_fraction + logic_area_fraction + reserved_area_fraction > 1.0:
        return None
    compute_budget_um2 = die_area_mm2 * 1_000_000.0 * logic_area_fraction
    measured_l1 = _measured_l1_overhead(measured_l1_profile, cluster_count)
    available_compute_budget_um2 = compute_budget_um2 - float(measured_l1["area_um2"])
    replica_count = int(available_compute_budget_um2 // float(candidate["block_area_um2"]))
    if replica_count < 1 or cluster_count > replica_count:
        return None

    layers = 32
    hidden_size = 4096
    attention_heads = 32
    kv_bits = 8
    kv_heads = _kv_heads(attention_heads=attention_heads, kv_sharing="gqa8")
    head_dim = hidden_size // attention_heads
    kv_width = kv_heads * head_dim
    kv_bytes_per_scalar = kv_bits / 8.0
    kv_cache_bytes = 2 * sequence_length * kv_width * kv_bytes_per_scalar * layers

    total_sram_bytes = _sram_capacity_bytes(
        die_area_mm2=die_area_mm2,
        sram_area_fraction=sram_area_fraction,
        usable_sram_fraction=usable_sram_fraction,
        bitcell_area_um2_per_bit=0.02,
    )
    local_capacity_bytes = int(total_sram_bytes * local_sram_fraction)
    shared_capacity_bytes = max(0, total_sram_bytes - local_capacity_bytes)
    local_resident_bytes = min(kv_cache_bytes, local_capacity_bytes)
    shared_resident_bytes = min(max(0, kv_cache_bytes - local_resident_bytes), shared_capacity_bytes)
    local_read_share = local_resident_bytes / kv_cache_bytes if kv_cache_bytes else 0.0
    shared_read_share = shared_resident_bytes / kv_cache_bytes if kv_cache_bytes else 0.0
    hbm_read_share = max(0.0, 1.0 - local_read_share - shared_read_share)

    block_macs_per_cycle = int(candidate["block_macs_per_cycle"])
    total_macs_per_cycle = replica_count * block_macs_per_cycle
    total_vector_ops_per_cycle = max(1, int(math.ceil(total_macs_per_cycle * vector_ops_per_mac)))
    active_clusters = min(cluster_count, _ceil_div(sequence_length, tile_tokens))
    replicas_per_cluster_floor = replica_count // cluster_count
    replicas_per_cluster_ceil = math.ceil(replica_count / cluster_count)
    per_cluster_macs = max(1, replicas_per_cluster_floor * block_macs_per_cycle)
    per_cluster_vector_ops = max(1, int(math.ceil(per_cluster_macs * vector_ops_per_mac)))

    clock_ns = max(float(candidate["block_clock_ns"]), float(measured_l1["clock_ns"]))
    raw_hbm_bw = _physical_hbm_bytes_per_cycle(
        stack_count=8,
        pseudo_channels_per_stack=16,
        pseudo_channel_width_bits=64,
        data_rate_mtps=9000,
        core_clock_ns=clock_ns,
    )
    effective_hbm_bw = raw_hbm_bw * 0.75
    active_banks = _active_banks(tile_tokens=tile_tokens, bank_interleave_tokens=16, bank_count=bank_count)
    aggregate_bank_bw = active_banks * 2048.0 * 0.75
    vc_gain = min(1.0, 0.85 + 0.05 * (4 - 1))
    aggregate_noc_bw = (noc_bandwidth_bytes_per_cycle / max(1, noc_hops)) * 0.85 * vc_gain

    concurrent_clusters = max(1, active_clusters)
    hbm_bw_per_cluster = max(1.0, effective_hbm_bw / concurrent_clusters)
    shared_bank_bw_per_cluster = max(1.0, aggregate_bank_bw / concurrent_clusters)
    noc_bw_per_cluster = max(1.0, aggregate_noc_bw / concurrent_clusters)
    local_bank_bw_per_cluster = max(
        1.0,
        aggregate_bank_bw * max(local_sram_fraction, 1.0 / concurrent_clusters) / concurrent_clusters,
    )

    qkv_macs = hidden_size * hidden_size + 2 * hidden_size * kv_width
    qkv_cycles = _ceil_div(qkv_macs, total_macs_per_cycle)
    tile_count = _ceil_div(sequence_length, tile_tokens)
    tile_waves = _ceil_div(tile_count, active_clusters)
    tiles_per_cluster_floor = tile_count // active_clusters
    tiles_per_cluster_ceil = math.ceil(tile_count / active_clusters)

    tile_qk_cycles = _ceil_div(tile_tokens * hidden_size, per_cluster_macs)
    tile_value_cycles = _ceil_div(tile_tokens * hidden_size, per_cluster_macs)
    tile_stats_cycles = _ceil_div(3 * attention_heads * tile_tokens, per_cluster_vector_ops)
    tile_attention_cycles = tile_qk_cycles + tile_stats_cycles + tile_value_cycles

    full_tile_bytes = 2 * tile_tokens * kv_width * kv_bytes_per_scalar
    tile_local_cycles = _ceil_div(full_tile_bytes * local_read_share, local_bank_bw_per_cluster)
    tile_shared_bank_cycles = _ceil_div(full_tile_bytes * shared_read_share, shared_bank_bw_per_cluster)
    tile_noc_cycles = _ceil_div(full_tile_bytes * shared_read_share, noc_bw_per_cluster) + noc_hops * 2
    tile_shared_path_cycles = max(tile_shared_bank_cycles, tile_noc_cycles)
    tile_hbm_cycles = _ceil_div(full_tile_bytes * hbm_read_share, hbm_bw_per_cluster)
    tile_memory_cycles = max(tile_local_cycles, tile_shared_path_cycles, tile_hbm_cycles)
    tile_service_cycles = max(tile_attention_cycles, tile_memory_cycles)

    stat_payload_bytes = attention_heads * 2 * reduction_scalar_bytes
    value_payload_bytes = hidden_size * reduction_scalar_bytes
    partial_payload_bytes = stat_payload_bytes + value_payload_bytes
    reduction_ops_per_partial = hidden_size + 2 * attention_heads
    if reduction_strategy == "centralized_tile":
        reduction_payload_bytes = tile_count * partial_payload_bytes
        local_reduce_cycles = 0
        reduction_vector_cycles = _ceil_div(tile_count * reduction_ops_per_partial, per_cluster_vector_ops)
    else:
        reduction_payload_bytes = active_clusters * partial_payload_bytes
        local_reduce_cycles = _ceil_div(tiles_per_cluster_ceil * reduction_ops_per_partial, per_cluster_vector_ops)
        reduction_vector_cycles = _ceil_div(
            max(1, active_clusters) * reduction_ops_per_partial,
            total_vector_ops_per_cycle,
        )
    reduction_stages, _ = _reduction_factor(reduction_strategy, active_clusters)
    reduction_noc_cycles = _ceil_div(reduction_payload_bytes, max(1.0, aggregate_noc_bw)) + reduction_stages * noc_hops * 2
    base_cross_tile_reduction_cycles = local_reduce_cycles + max(reduction_noc_cycles, reduction_vector_cycles)
    cross_tile_reduction_cycles = _ceil_div(base_cross_tile_reduction_cycles * reduction_cycle_multiplier, 1) + reducer_setup_cycles
    command_dispatch_cycles = tile_count * command_cycles_per_tile + tile_waves * command_cycles_per_wave

    kv_write_bytes = 2 * kv_width * kv_bytes_per_scalar
    kv_write_cycles = _ceil_div(kv_write_bytes, max(1.0, min(aggregate_bank_bw, aggregate_noc_bw)))
    layer_cycles = qkv_cycles + tile_waves * tile_service_cycles + command_dispatch_cycles + cross_tile_reduction_cycles + kv_write_cycles
    total_cycles = layer_cycles * layers
    dominant = max(
        {
            "tile_attention": tile_attention_cycles,
            "local_sram": tile_local_cycles,
            "shared_path": tile_shared_path_cycles,
            "hbm": tile_hbm_cycles,
            "cross_tile_reduction": cross_tile_reduction_cycles,
            "command_dispatch": command_dispatch_cycles,
        }.items(),
        key=lambda item: item[1],
    )[0]

    return {
        "label": "llama7b_proxy",
        "layers": layers,
        "hidden_size": hidden_size,
        "attention_heads": attention_heads,
        "sequence_length": sequence_length,
        "die_area_mm2": die_area_mm2,
        "kv_sharing": "gqa8",
        "kv_heads": kv_heads,
        "kv_bits": kv_bits,
        "kv_cache_mib": round(kv_cache_bytes / (1024 * 1024), 6),
        "sram_area_fraction": sram_area_fraction,
        "usable_sram_fraction": usable_sram_fraction,
        "local_sram_fraction": local_sram_fraction,
        "total_sram_mib": round(total_sram_bytes / (1024 * 1024), 6),
        "local_capacity_mib": round(local_capacity_bytes / (1024 * 1024), 6),
        "shared_capacity_mib": round(shared_capacity_bytes / (1024 * 1024), 6),
        "local_byte_share": round(local_read_share, 6),
        "shared_byte_share": round(shared_read_share, 6),
        "hbm_byte_share": round(hbm_read_share, 6),
        "bank_count": bank_count,
        "active_banks": active_banks,
        "noc_bandwidth_bytes_per_cycle": noc_bandwidth_bytes_per_cycle,
        "noc_hops": noc_hops,
        "aggregate_noc_effective_bytes_per_cycle": round(aggregate_noc_bw, 6),
        "per_cluster_noc_effective_bytes_per_cycle": round(noc_bw_per_cluster, 6),
        "raw_hbm_bytes_per_cycle": round(raw_hbm_bw, 6),
        "effective_hbm_bytes_per_cycle": round(effective_hbm_bw, 6),
        "per_cluster_hbm_bytes_per_cycle": round(hbm_bw_per_cluster, 6),
        "tile_tokens": tile_tokens,
        "tile_count": tile_count,
        "tile_waves": tile_waves,
        "tiles_per_cluster_floor": tiles_per_cluster_floor,
        "tiles_per_cluster_ceil": tiles_per_cluster_ceil,
        "cluster_count": cluster_count,
        "active_clusters": active_clusters,
        "replicas_per_cluster_floor": replicas_per_cluster_floor,
        "replicas_per_cluster_ceil": replicas_per_cluster_ceil,
        "compute_arch": candidate["compute_arch"],
        "compute_source": candidate.get("compute_source", "legacy_npu_block"),
        "compute_replica_count": replica_count,
        "compute_logic_area_fraction": logic_area_fraction,
        "reserved_area_fraction": reserved_area_fraction,
        "compute_budget_um2": round(compute_budget_um2, 6),
        "compute_array_budget_after_measured_l1_um2": round(available_compute_budget_um2, 6),
        "compute_area_um2": round(replica_count * float(candidate["block_area_um2"]), 6),
        "compute_power_mw": round(replica_count * float(candidate["block_power_mw"]), 6),
        "measured_l1_profile": measured_l1["profile"],
        "measured_l1_overhead_area_um2": round(float(measured_l1["area_um2"]), 6),
        "measured_l1_overhead_power_mw": round(float(measured_l1["power_mw"]), 6),
        "measured_l1_overhead_clock_ns": round(float(measured_l1["clock_ns"]), 6),
        "logic_area_used_um2": round(replica_count * float(candidate["block_area_um2"]) + float(measured_l1["area_um2"]), 6),
        "logic_area_slack_um2": round(
            compute_budget_um2 - replica_count * float(candidate["block_area_um2"]) - float(measured_l1["area_um2"]),
            6,
        ),
        "logic_power_mw": round(replica_count * float(candidate["block_power_mw"]) + float(measured_l1["power_mw"]), 6),
        "local_datapath_area_um2": round(float(measured_l1["local_datapath_area_um2"]), 6),
        "local_datapath_power_mw": round(float(measured_l1["local_datapath_power_mw"]), 6),
        "local_datapath_clock_ns": round(float(measured_l1["local_datapath_clock_ns"]), 6),
        "local_datapath_metrics_csv": measured_l1["local_datapath_metrics_csv"],
        "noc_fifo_area_um2": round(float(measured_l1["noc_fifo_area_um2"]), 6),
        "noc_fifo_power_mw": round(float(measured_l1["noc_fifo_power_mw"]), 6),
        "noc_fifo_clock_ns": round(float(measured_l1["noc_fifo_clock_ns"]), 6),
        "noc_fifo_per_cluster": measured_l1["fifo_per_cluster"],
        "noc_fifo_metrics_csv": measured_l1["noc_fifo_metrics_csv"],
        "noc_router_area_um2": round(float(measured_l1["noc_router_area_um2"]), 6),
        "noc_router_power_mw": round(float(measured_l1["noc_router_power_mw"]), 6),
        "noc_router_clock_ns": round(float(measured_l1["noc_router_clock_ns"]), 6),
        "noc_router_per_cluster": measured_l1["router_per_cluster"],
        "noc_router_metrics_csv": measured_l1["noc_router_metrics_csv"],
        "softmax_weight_generator_area_um2": round(float(measured_l1["softmax_weight_generator_area_um2"]), 6),
        "softmax_weight_generator_power_mw": round(float(measured_l1["softmax_weight_generator_power_mw"]), 6),
        "softmax_weight_generator_clock_ns": round(float(measured_l1["softmax_weight_generator_clock_ns"]), 6),
        "softmax_weight_generator_per_cluster": measured_l1["softmax_weight_generator_per_cluster"],
        "softmax_weight_generator_metrics_csv": measured_l1["softmax_weight_generator_metrics_csv"],
        "macs_per_cycle": total_macs_per_cycle,
        "vector_ops_per_cycle": total_vector_ops_per_cycle,
        "per_cluster_macs_per_cycle": per_cluster_macs,
        "per_cluster_vector_ops_per_cycle": per_cluster_vector_ops,
        "clock_ns": clock_ns,
        "qkv_cycles": qkv_cycles,
        "tile_qk_cycles": tile_qk_cycles,
        "tile_stats_cycles": tile_stats_cycles,
        "tile_value_cycles": tile_value_cycles,
        "tile_attention_cycles": tile_attention_cycles,
        "tile_local_sram_cycles": tile_local_cycles,
        "tile_shared_path_cycles": tile_shared_path_cycles,
        "tile_hbm_cycles": tile_hbm_cycles,
        "tile_memory_cycles": tile_memory_cycles,
        "tile_service_cycles": tile_service_cycles,
        "reduction_strategy": reduction_strategy,
        "reduction_scalar_bytes": reduction_scalar_bytes,
        "partial_reduction_payload_bytes": partial_payload_bytes,
        "cross_tile_reduction_payload_bytes": reduction_payload_bytes,
        "local_reduction_cycles": local_reduce_cycles,
        "cross_tile_reduction_noc_cycles": reduction_noc_cycles,
        "cross_tile_reduction_vector_cycles": reduction_vector_cycles,
        "base_cross_tile_reduction_cycles": base_cross_tile_reduction_cycles,
        "reduction_cycle_multiplier": reduction_cycle_multiplier,
        "reducer_setup_cycles": reducer_setup_cycles,
        "cross_tile_reduction_cycles": cross_tile_reduction_cycles,
        "command_cycles_per_tile": command_cycles_per_tile,
        "command_cycles_per_wave": command_cycles_per_wave,
        "command_dispatch_cycles": command_dispatch_cycles,
        "kv_write_cycles": kv_write_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
        "dominant_tile_resource": dominant,
        "measured_block_macs_per_cycle": candidate["block_macs_per_cycle"],
        "measured_block_clock_ns": candidate["block_clock_ns"],
        "measured_block_area_um2": candidate["block_area_um2"],
        "measured_block_power_mw": candidate["block_power_mw"],
        "metrics_csv": candidate["metrics_csv"],
        "metrics_tag": candidate["metrics_tag"],
        "metrics_param_hash": candidate["metrics_param_hash"],
        "dense_array_m": candidate.get("dense_array_m"),
        "dense_array_n": candidate.get("dense_array_n"),
        "dense_k_unroll": candidate.get("dense_k_unroll"),
        "dense_pipeline_stages": candidate.get("dense_pipeline_stages"),
        "vector_ops_per_mac_assumption": vector_ops_per_mac,
    }


def build_report(
    *,
    repo_root: Path,
    tag_substring: str,
    compute_source: str,
    sequence_length_list: list[int],
    die_area_mm2_list: list[float],
    sram_area_fraction_list: list[float],
    logic_area_fraction_list: list[float],
    reserved_area_fraction: float,
    usable_sram_fraction_list: list[float],
    local_sram_fraction_list: list[float],
    tile_tokens_list: list[int],
    bank_count_list: list[int],
    cluster_count_list: list[int],
    noc_bandwidth_bytes_per_cycle_list: list[float],
    noc_hops_list: list[int],
    reduction_strategy_list: list[str],
    vector_ops_per_mac: float,
    reduction_scalar_bytes: int,
    command_cycles_per_tile_list: list[int] | None = None,
    command_cycles_per_wave_list: list[int] | None = None,
    reducer_setup_cycles_list: list[int] | None = None,
    reduction_cycle_multiplier_list: list[float] | None = None,
    measured_l1_costs_path: Path | None = None,
    measured_l1_profile_list: list[str] | None = None,
    measured_l1_profiles: list[JsonDict | None] | None = None,
) -> JsonDict:
    candidates = _load_compute_candidates(
        repo_root=repo_root,
        tag_substring=tag_substring,
        compute_source=compute_source,
    )
    measured_l1_profiles = measured_l1_profiles or _load_measured_l1_profiles(
        repo_root=repo_root,
        costs_path=measured_l1_costs_path,
        profile_names=measured_l1_profile_list,
    )
    command_cycles_per_tile_list = command_cycles_per_tile_list or [0]
    command_cycles_per_wave_list = command_cycles_per_wave_list or [0]
    reducer_setup_cycles_list = reducer_setup_cycles_list or [0]
    reduction_cycle_multiplier_list = reduction_cycle_multiplier_list or [1.0]
    best: JsonDict | None = None
    top_rows_heap: list[tuple[float, int, JsonDict]] = []
    heap_counter = 0
    generated_row_count = 0
    skipped_area_budget = 0
    dominance: dict[str, int] = {}
    best_by_die: dict[tuple[Any, ...], JsonDict] = {}
    best_by_die_cluster: dict[tuple[Any, ...], JsonDict] = {}
    best_by_reduction_strategy: dict[tuple[Any, ...], JsonDict] = {}
    best_by_overhead: dict[tuple[Any, ...], JsonDict] = {}
    best_by_measured_l1_profile: dict[tuple[Any, ...], JsonDict] = {}
    best_by_memory_noc: dict[tuple[Any, ...], JsonDict] = {}
    for sequence_length in sequence_length_list:
        for die_area_mm2 in die_area_mm2_list:
            for sram_area_fraction in sram_area_fraction_list:
                for logic_area_fraction in logic_area_fraction_list:
                    for usable_sram_fraction in usable_sram_fraction_list:
                        for local_sram_fraction in local_sram_fraction_list:
                            for tile_tokens in tile_tokens_list:
                                for bank_count in bank_count_list:
                                    for cluster_count in cluster_count_list:
                                        for noc_bw in noc_bandwidth_bytes_per_cycle_list:
                                            for noc_hops in noc_hops_list:
                                                for reduction_strategy in reduction_strategy_list:
                                                    for command_cycles_per_tile in command_cycles_per_tile_list:
                                                        for command_cycles_per_wave in command_cycles_per_wave_list:
                                                            for reducer_setup_cycles in reducer_setup_cycles_list:
                                                                for reduction_cycle_multiplier in reduction_cycle_multiplier_list:
                                                                    for measured_l1_profile in measured_l1_profiles:
                                                                        for candidate in candidates:
                                                                            row = _shape_row(
                                                                                candidate=candidate,
                                                                                die_area_mm2=die_area_mm2,
                                                                                sram_area_fraction=sram_area_fraction,
                                                                                logic_area_fraction=logic_area_fraction,
                                                                                reserved_area_fraction=reserved_area_fraction,
                                                                                sequence_length=sequence_length,
                                                                                usable_sram_fraction=usable_sram_fraction,
                                                                                local_sram_fraction=local_sram_fraction,
                                                                                tile_tokens=tile_tokens,
                                                                                bank_count=bank_count,
                                                                                cluster_count=cluster_count,
                                                                                noc_bandwidth_bytes_per_cycle=noc_bw,
                                                                                noc_hops=noc_hops,
                                                                                reduction_strategy=reduction_strategy,
                                                                                vector_ops_per_mac=vector_ops_per_mac,
                                                                                reduction_scalar_bytes=reduction_scalar_bytes,
                                                                                command_cycles_per_tile=command_cycles_per_tile,
                                                                                command_cycles_per_wave=command_cycles_per_wave,
                                                                                reducer_setup_cycles=reducer_setup_cycles,
                                                                                reduction_cycle_multiplier=reduction_cycle_multiplier,
                                                                                measured_l1_profile=measured_l1_profile,
                                                                            )
                                                                            if row is None:
                                                                                skipped_area_budget += 1
                                                                            else:
                                                                                generated_row_count += 1
                                                                                resource = str(row["dominant_tile_resource"])
                                                                                dominance[resource] = dominance.get(resource, 0) + 1
                                                                                if best is None or row["latency_us"] < best["latency_us"]:
                                                                                    best = row
                                                                                heap_entry = (-float(row["latency_us"]), heap_counter, row)
                                                                                heap_counter += 1
                                                                                if len(top_rows_heap) < 50:
                                                                                    heapq.heappush(top_rows_heap, heap_entry)
                                                                                elif heap_entry[0] > top_rows_heap[0][0]:
                                                                                    heapq.heapreplace(top_rows_heap, heap_entry)
                                                                                _update_best_by(best_by_die, ("sequence_length", "die_area_mm2"), row)
                                                                                _update_best_by(
                                                                                    best_by_die_cluster,
                                                                                    ("sequence_length", "die_area_mm2", "cluster_count"),
                                                                                    row,
                                                                                )
                                                                                _update_best_by(
                                                                                    best_by_reduction_strategy,
                                                                                    ("sequence_length", "die_area_mm2", "reduction_strategy"),
                                                                                    row,
                                                                                )
                                                                                _update_best_by(
                                                                                    best_by_overhead,
                                                                                    (
                                                                                        "sequence_length",
                                                                                        "die_area_mm2",
                                                                                        "command_cycles_per_tile",
                                                                                        "command_cycles_per_wave",
                                                                                        "reducer_setup_cycles",
                                                                                        "reduction_cycle_multiplier",
                                                                                    ),
                                                                                    row,
                                                                                )
                                                                                _update_best_by(
                                                                                    best_by_measured_l1_profile,
                                                                                    ("sequence_length", "die_area_mm2", "measured_l1_profile"),
                                                                                    row,
                                                                                )
                                                                                _update_best_by(
                                                                                    best_by_memory_noc,
                                                                                    (
                                                                                        "sequence_length",
                                                                                        "die_area_mm2",
                                                                                        "sram_area_fraction",
                                                                                        "local_sram_fraction",
                                                                                        "bank_count",
                                                                                        "noc_bandwidth_bytes_per_cycle",
                                                                                        "noc_hops",
                                                                                        "reduction_strategy",
                                                                                    ),
                                                                                    row,
                                                                                )
    if best is None:
        raise RuntimeError("no rows generated; area budget or cluster count may be infeasible")
    top_rows = [entry[2] for entry in sorted(top_rows_heap, key=lambda entry: (entry[2]["latency_us"], entry[1]))]
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_clustered_schedule_llama7b_v1",
        "inputs": {
            "tag_substring": tag_substring,
            "compute_source": compute_source,
            "sequence_length_list": sequence_length_list,
            "die_area_mm2_list": die_area_mm2_list,
            "sram_area_fraction_list": sram_area_fraction_list,
            "logic_area_fraction_list": logic_area_fraction_list,
            "reserved_area_fraction": reserved_area_fraction,
            "usable_sram_fraction_list": usable_sram_fraction_list,
            "local_sram_fraction_list": local_sram_fraction_list,
            "tile_tokens_list": tile_tokens_list,
            "bank_count_list": bank_count_list,
            "cluster_count_list": cluster_count_list,
            "noc_bandwidth_bytes_per_cycle_list": noc_bandwidth_bytes_per_cycle_list,
            "noc_hops_list": noc_hops_list,
            "reduction_strategy_list": reduction_strategy_list,
            "vector_ops_per_mac": vector_ops_per_mac,
            "reduction_scalar_bytes": reduction_scalar_bytes,
            "command_cycles_per_tile_list": command_cycles_per_tile_list,
            "command_cycles_per_wave_list": command_cycles_per_wave_list,
            "reducer_setup_cycles_list": reducer_setup_cycles_list,
            "reduction_cycle_multiplier_list": reduction_cycle_multiplier_list,
            "measured_l1_costs_path": str(measured_l1_costs_path or ""),
            "measured_l1_profile_list": measured_l1_profile_list or [],
        },
        "measured_l1_profiles": [profile for profile in measured_l1_profiles if profile is not None],
        "compute_candidates": candidates,
        "sweep_summary": {
            "generated_row_count": generated_row_count,
            "skipped_area_budget_count": skipped_area_budget,
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
            "retained_row_count": (
                1
                + len(top_rows_heap)
                + len(best_by_die)
                + len(best_by_die_cluster)
                + len(best_by_reduction_strategy)
                + len(best_by_overhead)
                + len(best_by_measured_l1_profile)
                + len(best_by_memory_noc)
            ),
        },
        "best": best,
        "top_rows": top_rows,
        "best_by_die": _best_by_values(best_by_die, ("sequence_length", "die_area_mm2")),
        "best_by_die_cluster": _best_by_values(best_by_die_cluster, ("sequence_length", "die_area_mm2", "cluster_count")),
        "best_by_reduction_strategy": _best_by_values(
            best_by_reduction_strategy,
            ("sequence_length", "die_area_mm2", "reduction_strategy"),
        ),
        "best_by_overhead": _best_by_values(
            best_by_overhead,
            (
                "sequence_length",
                "die_area_mm2",
                "command_cycles_per_tile",
                "command_cycles_per_wave",
                "reducer_setup_cycles",
                "reduction_cycle_multiplier",
            ),
        ),
        "best_by_measured_l1_profile": _best_by_values(
            best_by_measured_l1_profile,
            ("sequence_length", "die_area_mm2", "measured_l1_profile"),
        ),
        "best_by_memory_noc": sorted(
            best_by_memory_noc.values(),
            key=lambda row: row["latency_us"],
        )[:200],
        "assumptions": [
            "One decode-token attention pass is split into sequence KV tiles.",
            "Tiles are statically assigned to active clusters by wave; each active cluster handles at most one tile per wave.",
            "Each tile produces softmax statistics and a partial value vector for the current token.",
            "Reduction strategies model cross-tile combination after tile service: centralized_tile sends every tile partial, owner_cluster and cluster_tree first reduce tiles locally per cluster.",
            "This is an analytic schedule model; it still does not model RTL command queues or cycle-accurate SRAM/NoC arbitration.",
            "Optional command and reducer overhead parameters are sensitivity knobs, not measured RTL/PPA.",
            "When measured L1 cost profiles are provided, their per-cluster tile/reducer, FIFO, and router area is subtracted from the logic budget before compute replicas are allocated.",
            "Measured L1 profile clock is combined by max() with measured compute-array clock; this is a conservative local macro proxy, not a full routed SoC timing closure.",
            "Measured L1 profiles charge the local tile/value datapath, optional softmax-weight generator, and memory/NoC primitives listed in the selected cost file; cycle-accurate SRAM/NoC arbitration remains an analytic service model.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Decoder Attention/KV Clustered Schedule",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- skipped_area_budget_count: `{payload['sweep_summary']['skipped_area_budget_count']}`",
        "",
        "## Best",
        "",
        "| seq | die | SRAM | logic | L1 profile | arch | replicas | clusters | reduction | tile | clock ns | latency us | resource |",
        "|---:|---:|---:|---:|---|---|---:|---:|---|---:|---:|---:|---|",
        "| {seq} | {die} | {sram} | {logic} | {l1} | {arch} | {rep} | {cluster} | {red} | {tile} | {clk} | {lat} | {res} |".format(
            seq=best["sequence_length"],
            die=best["die_area_mm2"],
            sram=best["sram_area_fraction"],
            logic=best["compute_logic_area_fraction"],
            l1=best["measured_l1_profile"],
            arch=best["compute_arch"],
            rep=best["compute_replica_count"],
            cluster=best["cluster_count"],
            red=best["reduction_strategy"],
            tile=best["tile_tokens"],
            clk=best["clock_ns"],
            lat=best["latency_us"],
            res=best["dominant_tile_resource"],
        ),
        "",
        "## Best By Overhead",
        "",
        "| die | cmd/tile | cmd/wave | reducer setup | reduction x | clusters | reduction | latency us | resource |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in payload["best_by_overhead"]:
        lines.append(
            "| {die} | {ct} | {cw} | {setup} | {mult} | {cluster} | {red} | {lat} | {res} |".format(
                die=row["die_area_mm2"],
                ct=row["command_cycles_per_tile"],
                cw=row["command_cycles_per_wave"],
                setup=row["reducer_setup_cycles"],
                mult=row["reduction_cycle_multiplier"],
                cluster=row["cluster_count"],
                red=row["reduction_strategy"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend([
        "",
        "## Best By Measured L1 Profile",
        "",
        "| die | L1 profile | logic used um2 | replicas | clusters | reduction | latency us | resource |",
        "|---:|---|---:|---:|---:|---|---:|---|",
    ])
    for row in payload["best_by_measured_l1_profile"]:
        lines.append(
            "| {die} | {l1} | {used} | {rep} | {cluster} | {red} | {lat} | {res} |".format(
                die=row["die_area_mm2"],
                l1=row["measured_l1_profile"],
                used=row["logic_area_used_um2"],
                rep=row["compute_replica_count"],
                cluster=row["cluster_count"],
                red=row["reduction_strategy"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend([
        "",
        "## Best By Die And Cluster",
        "",
        "| die | clusters | arch | replicas | reduction | tile waves | tile service | reduction cycles | latency us | resource |",
        "|---:|---:|---|---:|---|---:|---:|---:|---:|---|",
    ])
    for row in payload["best_by_die_cluster"]:
        lines.append(
            "| {die} | {cluster} | {arch} | {rep} | {red} | {waves} | {service} | {reduce} | {lat} | {res} |".format(
                die=row["die_area_mm2"],
                cluster=row["cluster_count"],
                arch=row["compute_arch"],
                rep=row["compute_replica_count"],
                red=row["reduction_strategy"],
                waves=row["tile_waves"],
                service=row["tile_service_cycles"],
                reduce=row["cross_tile_reduction_cycles"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    allowed = {"centralized_tile", "owner_cluster", "cluster_tree"}
    if not items or any(item not in allowed for item in items):
        raise argparse.ArgumentTypeError(f"expected comma-separated values from {sorted(allowed)}")
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--tag-substring", default="compute_stability_cmp33")
    ap.add_argument(
        "--compute-source",
        choices=["legacy_npu_block", "dense_gemm_tile", "all"],
        default="legacy_npu_block",
    )
    ap.add_argument("--sequence-length-list", type=_int_list, default=[131072])
    ap.add_argument("--die-area-mm2-list", type=_float_list, default=[100, 200, 400, 800, 1200])
    ap.add_argument("--sram-area-fraction", type=_float_list, default=[0.4, 0.6, 0.75])
    ap.add_argument("--logic-area-fraction", type=_float_list, default=[0.05, 0.1, 0.2])
    ap.add_argument("--reserved-area-fraction", type=float, default=0.1)
    ap.add_argument("--usable-sram-fraction", type=_float_list, default=[0.7, 0.85])
    ap.add_argument("--local-sram-fraction", type=_float_list, default=[0.1, 0.25, 0.5])
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[256, 512, 1024])
    ap.add_argument("--bank-count", type=_int_list, default=[16, 64])
    ap.add_argument("--cluster-count", type=_int_list, default=[1, 2, 4, 8, 16])
    ap.add_argument("--noc-bandwidth-bytes-per-cycle", type=_float_list, default=[8192, 32768, 131072])
    ap.add_argument("--noc-hops", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--reduction-strategy", type=_str_list, default=["owner_cluster", "cluster_tree", "centralized_tile"])
    ap.add_argument("--vector-ops-per-mac", type=float, default=0.125)
    ap.add_argument("--reduction-scalar-bytes", type=int, default=2)
    ap.add_argument("--command-cycles-per-tile", type=_int_list, default=[0])
    ap.add_argument("--command-cycles-per-wave", type=_int_list, default=[0])
    ap.add_argument("--reducer-setup-cycles", type=_int_list, default=[0])
    ap.add_argument("--reduction-cycle-multiplier", type=_float_list, default=[1.0])
    ap.add_argument("--measured-l1-costs", default="")
    ap.add_argument("--measured-l1-profile", type=_profile_list, default=["all"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        repo_root=Path(args.repo_root),
        tag_substring=args.tag_substring,
        compute_source=args.compute_source,
        sequence_length_list=args.sequence_length_list,
        die_area_mm2_list=args.die_area_mm2_list,
        sram_area_fraction_list=args.sram_area_fraction,
        logic_area_fraction_list=args.logic_area_fraction,
        reserved_area_fraction=args.reserved_area_fraction,
        usable_sram_fraction_list=args.usable_sram_fraction,
        local_sram_fraction_list=args.local_sram_fraction,
        tile_tokens_list=args.tile_tokens_list,
        bank_count_list=args.bank_count,
        cluster_count_list=args.cluster_count,
        noc_bandwidth_bytes_per_cycle_list=args.noc_bandwidth_bytes_per_cycle,
        noc_hops_list=args.noc_hops,
        reduction_strategy_list=args.reduction_strategy,
        vector_ops_per_mac=args.vector_ops_per_mac,
        reduction_scalar_bytes=args.reduction_scalar_bytes,
        command_cycles_per_tile_list=args.command_cycles_per_tile,
        command_cycles_per_wave_list=args.command_cycles_per_wave,
        reducer_setup_cycles_list=args.reducer_setup_cycles,
        reduction_cycle_multiplier_list=args.reduction_cycle_multiplier,
        measured_l1_costs_path=Path(args.measured_l1_costs) if args.measured_l1_costs else None,
        measured_l1_profile_list=args.measured_l1_profile,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

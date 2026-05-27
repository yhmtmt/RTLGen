#!/usr/bin/env python3
"""Estimate Llama7B attention/KV with measured compute blocks under clustered partitioning."""

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

from npu.eval.estimate_llm_decoder_attention_kv_measured_compute import (  # noqa: E402
    _best_by,
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


def _partitioned_shape_row(
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
    vector_ops_per_mac: float,
) -> JsonDict | None:
    if sram_area_fraction + logic_area_fraction + reserved_area_fraction > 1.0:
        return None
    compute_budget_um2 = die_area_mm2 * 1_000_000.0 * logic_area_fraction
    replica_count = int(compute_budget_um2 // float(candidate["block_area_um2"]))
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

    clock_ns = float(candidate["block_clock_ns"])
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
    local_bank_bw_per_cluster = max(1.0, aggregate_bank_bw * max(local_sram_fraction, 1.0 / concurrent_clusters) / concurrent_clusters)

    qkv_macs = hidden_size * hidden_size + 2 * hidden_size * kv_width
    qkv_cycles = _ceil_div(qkv_macs, total_macs_per_cycle)
    tile_count = _ceil_div(sequence_length, tile_tokens)
    tile_waves = _ceil_div(tile_count, active_clusters)

    tile_compute_cycles = _ceil_div(2 * tile_tokens * hidden_size, per_cluster_macs)
    tile_softmax_cycles = _ceil_div(5 * attention_heads * tile_tokens, per_cluster_vector_ops)
    tile_attention_cycles = tile_compute_cycles + tile_softmax_cycles

    full_tile_bytes = 2 * tile_tokens * kv_width * kv_bytes_per_scalar
    tile_local_cycles = _ceil_div(full_tile_bytes * local_read_share, local_bank_bw_per_cluster)
    tile_shared_bank_cycles = _ceil_div(full_tile_bytes * shared_read_share, shared_bank_bw_per_cluster)
    tile_noc_cycles = _ceil_div(full_tile_bytes * shared_read_share, noc_bw_per_cluster) + noc_hops * 2
    tile_shared_path_cycles = max(tile_shared_bank_cycles, tile_noc_cycles)
    tile_hbm_cycles = _ceil_div(full_tile_bytes * hbm_read_share, hbm_bw_per_cluster)
    tile_memory_cycles = max(tile_local_cycles, tile_shared_path_cycles, tile_hbm_cycles)
    tile_service_cycles = max(tile_attention_cycles, tile_memory_cycles)

    kv_write_bytes = 2 * kv_width * kv_bytes_per_scalar
    kv_write_cycles = _ceil_div(kv_write_bytes, max(1.0, min(aggregate_bank_bw, aggregate_noc_bw)))
    layer_cycles = qkv_cycles + tile_waves * tile_service_cycles + kv_write_cycles
    total_cycles = layer_cycles * layers
    dominant = max(
        {
            "tile_attention": tile_attention_cycles,
            "local_sram": tile_local_cycles,
            "shared_path": tile_shared_path_cycles,
            "hbm": tile_hbm_cycles,
        }.items(),
        key=lambda item: item[1],
    )[0]
    ideal_cluster_cycles = tile_count * tile_attention_cycles / concurrent_clusters if concurrent_clusters else 0.0
    realized_tile_cycles = tile_waves * tile_service_cycles

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
        "cluster_count": cluster_count,
        "active_clusters": active_clusters,
        "replicas_per_cluster_floor": replicas_per_cluster_floor,
        "replicas_per_cluster_ceil": replicas_per_cluster_ceil,
        "compute_arch": candidate["compute_arch"],
        "compute_replica_count": replica_count,
        "compute_logic_area_fraction": logic_area_fraction,
        "reserved_area_fraction": reserved_area_fraction,
        "compute_budget_um2": round(compute_budget_um2, 6),
        "compute_area_um2": round(replica_count * float(candidate["block_area_um2"]), 6),
        "compute_power_mw": round(replica_count * float(candidate["block_power_mw"]), 6),
        "macs_per_cycle": total_macs_per_cycle,
        "vector_ops_per_cycle": total_vector_ops_per_cycle,
        "per_cluster_macs_per_cycle": per_cluster_macs,
        "per_cluster_vector_ops_per_cycle": per_cluster_vector_ops,
        "clock_ns": clock_ns,
        "qkv_cycles": qkv_cycles,
        "tile_attention_cycles": tile_attention_cycles,
        "tile_local_sram_cycles": tile_local_cycles,
        "tile_shared_path_cycles": tile_shared_path_cycles,
        "tile_hbm_cycles": tile_hbm_cycles,
        "tile_memory_cycles": tile_memory_cycles,
        "tile_service_cycles": tile_service_cycles,
        "kv_write_cycles": kv_write_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "latency_us": round(total_cycles * clock_ns / 1000.0, 6),
        "dominant_tile_resource": dominant,
        "cluster_tile_efficiency": round(ideal_cluster_cycles / realized_tile_cycles, 6) if realized_tile_cycles else 0.0,
        "measured_block_macs_per_cycle": candidate["block_macs_per_cycle"],
        "measured_block_clock_ns": candidate["block_clock_ns"],
        "measured_block_area_um2": candidate["block_area_um2"],
        "measured_block_power_mw": candidate["block_power_mw"],
        "metrics_csv": candidate["metrics_csv"],
        "metrics_tag": candidate["metrics_tag"],
        "metrics_param_hash": candidate["metrics_param_hash"],
        "vector_ops_per_mac_assumption": vector_ops_per_mac,
    }


def build_report(
    *,
    repo_root: Path,
    tag_substring: str,
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
    vector_ops_per_mac: float,
) -> JsonDict:
    candidates = _load_compute_candidates(repo_root=repo_root, tag_substring=tag_substring)
    rows: list[JsonDict] = []
    skipped_area_budget = 0
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
                                                for candidate in candidates:
                                                    row = _partitioned_shape_row(
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
                                                        vector_ops_per_mac=vector_ops_per_mac,
                                                    )
                                                    if row is None:
                                                        skipped_area_budget += 1
                                                    else:
                                                        rows.append(row)
    if not rows:
        raise RuntimeError("no rows generated; area budget or cluster count may be infeasible")
    rows_sorted = sorted(rows, key=lambda row: row["latency_us"])
    dominance: dict[str, int] = {}
    for row in rows:
        key = str(row["dominant_tile_resource"])
        dominance[key] = dominance.get(key, 0) + 1
    best_by_memory_noc = _best_by(
        rows,
        (
            "sequence_length",
            "die_area_mm2",
            "sram_area_fraction",
            "local_sram_fraction",
            "bank_count",
            "noc_bandwidth_bytes_per_cycle",
            "noc_hops",
        ),
    )
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_measured_compute_partition_llama7b_v1",
        "inputs": {
            "tag_substring": tag_substring,
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
            "vector_ops_per_mac": vector_ops_per_mac,
        },
        "compute_candidates": candidates,
        "sweep_summary": {
            "generated_row_count": len(rows),
            "skipped_area_budget_count": skipped_area_budget,
            "dominant_tile_resource_counts": dict(sorted(dominance.items())),
        },
        "best": rows_sorted[0],
        "top_rows": rows_sorted[:50],
        "best_by_die": _best_by(rows, ("sequence_length", "die_area_mm2")),
        "best_by_die_cluster": _best_by(rows, ("sequence_length", "die_area_mm2", "cluster_count")),
        "best_by_die_sram_logic": _best_by(
            rows,
            ("sequence_length", "die_area_mm2", "sram_area_fraction", "compute_logic_area_fraction"),
        ),
        "best_by_compute_arch": _best_by(rows, ("sequence_length", "die_area_mm2", "compute_arch")),
        "best_by_memory_noc": sorted(best_by_memory_noc, key=lambda row: row["latency_us"])[:200],
        "assumptions": [
            "Compute blocks use merged corrected NPU PPA rows and are replicated within the logic area budget.",
            "cluster_count is a planning partition count; replicas are statically assigned to clusters by floor/ceil division.",
            "Attention tiles are sequence-sharded across active clusters; qkv projection uses aggregate compute throughput.",
            "Local SRAM is modeled as sequence-sharded resident KV storage; shared SRAM and HBM bandwidth are contended across active clusters.",
            "NoC bandwidth is divided across active clusters and penalized by hop count plus router latency.",
            "This is a scheduling/service model, not cycle-accurate NoC arbitration or SRAM macro floorplanning.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Decoder Attention/KV Measured Compute Partition",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- skipped_area_budget_count: `{payload['sweep_summary']['skipped_area_budget_count']}`",
        "",
        "## Best",
        "",
        "| seq | die | SRAM | logic | arch | replicas | clusters | MAC/cyc | clock ns | latency us | resource |",
        "|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|",
        "| {seq} | {die} | {sram} | {logic} | {arch} | {rep} | {cluster} | {macs} | {clk} | {lat} | {res} |".format(
            seq=best["sequence_length"],
            die=best["die_area_mm2"],
            sram=best["sram_area_fraction"],
            logic=best["compute_logic_area_fraction"],
            arch=best["compute_arch"],
            rep=best["compute_replica_count"],
            cluster=best["cluster_count"],
            macs=best["macs_per_cycle"],
            clk=best["clock_ns"],
            lat=best["latency_us"],
            res=best["dominant_tile_resource"],
        ),
        "",
        "## Best By Die",
        "",
        "| seq | die | SRAM | logic | arch | replicas | clusters | local share | shared share | hbm share | latency us | resource |",
        "|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["best_by_die"]:
        lines.append(
            "| {seq} | {die} | {sram} | {logic} | {arch} | {rep} | {cluster} | {local} | {shared} | {hbm} | {lat} | {res} |".format(
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                sram=row["sram_area_fraction"],
                logic=row["compute_logic_area_fraction"],
                arch=row["compute_arch"],
                rep=row["compute_replica_count"],
                cluster=row["cluster_count"],
                local=row["local_byte_share"],
                shared=row["shared_byte_share"],
                hbm=row["hbm_byte_share"],
                lat=row["latency_us"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend(
        [
            "",
            "## Best By Die And Cluster",
            "",
            "| die | clusters | arch | replicas | per-cluster MAC/cyc | latency us | efficiency | resource |",
            "|---:|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["best_by_die_cluster"]:
        lines.append(
            "| {die} | {cluster} | {arch} | {rep} | {pcmac} | {lat} | {eff} | {res} |".format(
                die=row["die_area_mm2"],
                cluster=row["cluster_count"],
                arch=row["compute_arch"],
                rep=row["compute_replica_count"],
                pcmac=row["per_cluster_macs_per_cycle"],
                lat=row["latency_us"],
                eff=row["cluster_tile_efficiency"],
                res=row["dominant_tile_resource"],
            )
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--tag-substring", default="compute_stability_cmp33")
    ap.add_argument("--sequence-length-list", type=_int_list, default=[131072])
    ap.add_argument("--die-area-mm2-list", type=_float_list, default=[100, 200, 400, 800, 1200])
    ap.add_argument("--sram-area-fraction", type=_float_list, default=[0.4, 0.6, 0.75])
    ap.add_argument("--logic-area-fraction", type=_float_list, default=[0.05, 0.1, 0.2])
    ap.add_argument("--reserved-area-fraction", type=float, default=0.1)
    ap.add_argument("--usable-sram-fraction", type=_float_list, default=[0.7, 0.85])
    ap.add_argument("--local-sram-fraction", type=_float_list, default=[0.1, 0.25, 0.5])
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[512, 1024])
    ap.add_argument("--bank-count", type=_int_list, default=[16, 64])
    ap.add_argument("--cluster-count", type=_int_list, default=[1, 2, 4, 8, 16, 32, 64])
    ap.add_argument("--noc-bandwidth-bytes-per-cycle", type=_float_list, default=[8192, 32768, 131072])
    ap.add_argument("--noc-hops", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--vector-ops-per-mac", type=float, default=0.125)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        repo_root=Path(args.repo_root),
        tag_substring=args.tag_substring,
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
        vector_ops_per_mac=args.vector_ops_per_mac,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(Path(args.out_md), payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

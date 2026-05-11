#!/usr/bin/env python3
"""Estimate decoder attention/KV memory hierarchy pressure."""

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
    if any(item <= 0.0 for item in parsed):
        raise argparse.ArgumentTypeError("all list items must be positive")
    return parsed


def _str_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated string list")
    return items


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _ceil_div(numerator: float, denominator: float) -> int:
    return int(math.ceil(numerator / denominator)) if numerator else 0


def _kv_heads(*, attention_heads: int, kv_sharing: str) -> int:
    if kv_sharing == "mha":
        return attention_heads
    if kv_sharing == "gqa4":
        return max(1, math.ceil(attention_heads / 4))
    if kv_sharing == "gqa8":
        return max(1, math.ceil(attention_heads / 8))
    if kv_sharing == "mqa":
        return 1
    raise ValueError(f"unsupported kv sharing model: {kv_sharing}")


def _stage(
    *,
    name: str,
    macs: int,
    vector_ops: int,
    activation_bytes: int,
    weight_bytes: int,
    kv_read_bytes: int,
    kv_write_bytes: int,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    weight_bandwidth_bytes_per_cycle: float,
    activation_bandwidth_bytes_per_cycle: float,
    kv_bandwidth_bytes_per_cycle: float,
    clock_ns: float,
    charge_weights: bool,
) -> JsonDict:
    weight_charged = weight_bytes if charge_weights else 0
    compute_work = macs + vector_ops
    compute_rate = macs_per_cycle if macs >= vector_ops else vector_ops_per_cycle
    compute_cycles = _ceil_div(compute_work, compute_rate)
    activation_cycles = _ceil_div(activation_bytes, activation_bandwidth_bytes_per_cycle)
    weight_cycles = _ceil_div(weight_charged, weight_bandwidth_bytes_per_cycle)
    kv_cycles = _ceil_div(kv_read_bytes + kv_write_bytes, kv_bandwidth_bytes_per_cycle)
    memory_cycles = max(activation_cycles, weight_cycles, kv_cycles)
    cycles = max(compute_cycles, memory_cycles)
    return {
        "stage": name,
        "macs": macs,
        "vector_ops": vector_ops,
        "activation_bytes": activation_bytes,
        "weight_bytes": weight_bytes,
        "charged_weight_bytes": weight_charged,
        "kv_read_bytes": kv_read_bytes,
        "kv_write_bytes": kv_write_bytes,
        "charged_bytes": activation_bytes + weight_charged + kv_read_bytes + kv_write_bytes,
        "compute_cycles": compute_cycles,
        "activation_cycles": activation_cycles,
        "weight_cycles": weight_cycles,
        "kv_cycles": kv_cycles,
        "memory_cycles": memory_cycles,
        "cycles": cycles,
        "latency_us": round(cycles * clock_ns / 1000.0, 6),
        "limiter": "memory" if memory_cycles >= compute_cycles else "compute",
    }


def _shape_rows(
    *,
    label: str,
    layers: int,
    hidden_size: int,
    attention_heads: int,
    sequence_length: int,
    kv_sharing: str,
    kv_memory_tier: str,
    kv_bandwidth_bytes_per_cycle: float,
    noc_bandwidth_bytes_per_cycle: float,
    noc_hops: int,
    macs_per_cycle: int,
    vector_ops_per_cycle: int,
    weight_bandwidth_bytes_per_cycle: float,
    activation_bandwidth_bytes_per_cycle: float,
    clock_ns: float,
    weight_bits: int,
    activation_bits: int,
    kv_bits: int,
    score_bits: int,
    weight_residency: str,
) -> JsonDict:
    h = hidden_size
    heads = attention_heads
    head_dim = h // heads
    kv_heads = _kv_heads(attention_heads=heads, kv_sharing=kv_sharing)
    kv_width = kv_heads * head_dim
    s = sequence_length
    charge_weights = weight_residency == "streaming_weights"

    weight_b = _byte_width(weight_bits)
    act_b = _byte_width(activation_bits)
    kv_b = _byte_width(kv_bits)
    score_b = _byte_width(score_bits)

    effective_kv_bw = kv_bandwidth_bytes_per_cycle
    if noc_hops > 0:
        effective_kv_bw = min(effective_kv_bw, noc_bandwidth_bytes_per_cycle / noc_hops)

    q_proj_macs = h * h
    kv_proj_macs = 2 * h * kv_width
    qkv_weight_bytes = (q_proj_macs + kv_proj_macs) * weight_b
    qkv_activation_bytes = (h + h + (2 * kv_width)) * act_b

    kv_read_bytes = 2 * s * kv_width * kv_b
    score_bytes = heads * s * score_b
    stages = [
        _stage(
            name="qkv_projection",
            macs=q_proj_macs + kv_proj_macs,
            vector_ops=0,
            activation_bytes=qkv_activation_bytes,
            weight_bytes=qkv_weight_bytes,
            kv_read_bytes=0,
            kv_write_bytes=0,
            macs_per_cycle=macs_per_cycle,
            vector_ops_per_cycle=vector_ops_per_cycle,
            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
            kv_bandwidth_bytes_per_cycle=effective_kv_bw,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="kv_cache_write",
            macs=0,
            vector_ops=0,
            activation_bytes=0,
            weight_bytes=0,
            kv_read_bytes=0,
            kv_write_bytes=2 * kv_width * kv_b,
            macs_per_cycle=macs_per_cycle,
            vector_ops_per_cycle=vector_ops_per_cycle,
            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
            kv_bandwidth_bytes_per_cycle=effective_kv_bw,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="qk_score",
            macs=s * h,
            vector_ops=0,
            activation_bytes=h * act_b,
            weight_bytes=0,
            kv_read_bytes=s * kv_width * kv_b,
            kv_write_bytes=score_bytes,
            macs_per_cycle=macs_per_cycle,
            vector_ops_per_cycle=vector_ops_per_cycle,
            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
            kv_bandwidth_bytes_per_cycle=effective_kv_bw,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="softmax_scores",
            macs=0,
            vector_ops=5 * heads * s,
            activation_bytes=2 * score_bytes,
            weight_bytes=0,
            kv_read_bytes=0,
            kv_write_bytes=0,
            macs_per_cycle=macs_per_cycle,
            vector_ops_per_cycle=vector_ops_per_cycle,
            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
            kv_bandwidth_bytes_per_cycle=effective_kv_bw,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="value_mix",
            macs=s * h,
            vector_ops=0,
            activation_bytes=score_bytes + h * act_b,
            weight_bytes=0,
            kv_read_bytes=s * kv_width * kv_b,
            kv_write_bytes=0,
            macs_per_cycle=macs_per_cycle,
            vector_ops_per_cycle=vector_ops_per_cycle,
            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
            kv_bandwidth_bytes_per_cycle=effective_kv_bw,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="attention_output_projection",
            macs=h * h,
            vector_ops=0,
            activation_bytes=2 * h * act_b,
            weight_bytes=h * h * weight_b,
            kv_read_bytes=0,
            kv_write_bytes=0,
            macs_per_cycle=macs_per_cycle,
            vector_ops_per_cycle=vector_ops_per_cycle,
            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
            kv_bandwidth_bytes_per_cycle=effective_kv_bw,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
    ]
    for stage in stages:
        for key in (
            "macs",
            "vector_ops",
            "activation_bytes",
            "weight_bytes",
            "charged_weight_bytes",
            "kv_read_bytes",
            "kv_write_bytes",
            "charged_bytes",
            "compute_cycles",
            "activation_cycles",
            "weight_cycles",
            "kv_cycles",
            "memory_cycles",
            "cycles",
        ):
            stage[key] *= layers
        stage["latency_us"] = round(stage["cycles"] * clock_ns / 1000.0, 6)

    total_cycles = sum(stage["cycles"] for stage in stages)
    total_bytes = sum(stage["charged_bytes"] for stage in stages)
    total_macs = sum(stage["macs"] for stage in stages)
    total_kv_read = sum(stage["kv_read_bytes"] for stage in stages)
    for stage in stages:
        stage["cycle_share"] = round(stage["cycles"] / total_cycles, 6) if total_cycles else 0.0
        stage["byte_share"] = round(stage["charged_bytes"] / total_bytes, 6) if total_bytes else 0.0
    dominant = max(stages, key=lambda row: row["cycles"])
    kv_cycle_share = sum(stage["cycles"] for stage in stages if stage["kv_cycles"] >= stage["compute_cycles"])
    return {
        "label": label,
        "layers": layers,
        "hidden_size": hidden_size,
        "attention_heads": attention_heads,
        "head_dim": head_dim,
        "sequence_length": sequence_length,
        "kv_sharing": kv_sharing,
        "kv_heads": kv_heads,
        "kv_bits": kv_bits,
        "kv_memory_tier": kv_memory_tier,
        "kv_bandwidth_bytes_per_cycle": kv_bandwidth_bytes_per_cycle,
        "noc_bandwidth_bytes_per_cycle": noc_bandwidth_bytes_per_cycle,
        "noc_hops": noc_hops,
        "effective_kv_bandwidth_bytes_per_cycle": round(effective_kv_bw, 6),
        "macs_per_cycle": macs_per_cycle,
        "vector_ops_per_cycle": vector_ops_per_cycle,
        "weight_residency": weight_residency,
        "total_cycles": total_cycles,
        "total_latency_us": round(total_cycles * clock_ns / 1000.0, 6),
        "total_macs": total_macs,
        "total_charged_bytes": total_bytes,
        "total_kv_read_bytes": total_kv_read,
        "kv_read_byte_share": round(total_kv_read / total_bytes, 6) if total_bytes else 0.0,
        "attention_arithmetic_intensity_macs_per_byte": round(total_macs / total_bytes, 6) if total_bytes else 0.0,
        "kv_limited_cycle_share": round(kv_cycle_share / total_cycles, 6) if total_cycles else 0.0,
        "dominant_substage": dominant["stage"],
        "dominant_substage_share": dominant["cycle_share"],
        "stages": stages,
    }


def _compact_row(row: JsonDict) -> JsonDict:
    return {
        "label": row["label"],
        "layers": row["layers"],
        "hidden_size": row["hidden_size"],
        "attention_heads": row["attention_heads"],
        "sequence_length": row["sequence_length"],
        "kv_sharing": row["kv_sharing"],
        "kv_heads": row["kv_heads"],
        "kv_bits": row["kv_bits"],
        "kv_memory_tier": row["kv_memory_tier"],
        "noc_hops": row["noc_hops"],
        "effective_kv_bandwidth_bytes_per_cycle": row["effective_kv_bandwidth_bytes_per_cycle"],
        "macs_per_cycle": row["macs_per_cycle"],
        "weight_residency": row["weight_residency"],
        "total_latency_us": row["total_latency_us"],
        "total_macs": row["total_macs"],
        "total_charged_bytes": row["total_charged_bytes"],
        "total_kv_read_bytes": row["total_kv_read_bytes"],
        "kv_read_byte_share": row["kv_read_byte_share"],
        "kv_limited_cycle_share": row["kv_limited_cycle_share"],
        "attention_arithmetic_intensity_macs_per_byte": row["attention_arithmetic_intensity_macs_per_byte"],
        "dominant_substage": row["dominant_substage"],
        "dominant_substage_share": row["dominant_substage_share"],
    }


def build_report(
    *,
    sequence_length_list: list[int],
    macs_per_cycle_list: list[int],
    kv_memory_tier_list: list[str],
    kv_sharing_list: list[str],
    kv_bits_list: list[int],
    noc_hops_list: list[int],
    clock_ns: float,
    weight_bits: int,
    activation_bits: int,
    score_bits: int,
    vector_ops_per_cycle: int,
    weight_bandwidth_bytes_per_cycle: float,
    activation_bandwidth_bytes_per_cycle: float,
    noc_bandwidth_bytes_per_cycle: float,
    include_detail: bool = False,
) -> JsonDict:
    shapes = [
        {"label": "gpt2_small", "layers": 12, "hidden_size": 768, "attention_heads": 12},
        {"label": "gpt2_medium_proxy", "layers": 24, "hidden_size": 1024, "attention_heads": 16},
        {"label": "llama7b_proxy", "layers": 32, "hidden_size": 4096, "attention_heads": 32},
        {"label": "large_context_proxy", "layers": 40, "hidden_size": 5120, "attention_heads": 40},
    ]
    tier_bandwidths = {
        "local_sram": 1024.0,
        "shared_sram": 256.0,
        "hbm": 64.0,
        "remote_hbm": 32.0,
    }
    rows: list[JsonDict] = []
    for shape in shapes:
        for sequence_length in sequence_length_list:
            for macs_per_cycle in macs_per_cycle_list:
                for kv_memory_tier in kv_memory_tier_list:
                    if kv_memory_tier not in tier_bandwidths:
                        raise ValueError(f"unsupported kv memory tier: {kv_memory_tier}")
                    for kv_sharing in kv_sharing_list:
                        for kv_bits in kv_bits_list:
                            for noc_hops in noc_hops_list:
                                if kv_memory_tier == "local_sram" and noc_hops != 0:
                                    continue
                                if kv_memory_tier != "local_sram" and noc_hops == 0:
                                    continue
                                for weight_residency in ["resident_weights", "streaming_weights"]:
                                    rows.append(
                                        _shape_rows(
                                            label=shape["label"],
                                            layers=shape["layers"],
                                            hidden_size=shape["hidden_size"],
                                            attention_heads=shape["attention_heads"],
                                            sequence_length=sequence_length,
                                            kv_sharing=kv_sharing,
                                            kv_memory_tier=kv_memory_tier,
                                            kv_bandwidth_bytes_per_cycle=tier_bandwidths[kv_memory_tier],
                                            noc_bandwidth_bytes_per_cycle=noc_bandwidth_bytes_per_cycle,
                                            noc_hops=noc_hops,
                                            macs_per_cycle=macs_per_cycle,
                                            vector_ops_per_cycle=vector_ops_per_cycle,
                                            weight_bandwidth_bytes_per_cycle=weight_bandwidth_bytes_per_cycle,
                                            activation_bandwidth_bytes_per_cycle=activation_bandwidth_bytes_per_cycle,
                                            clock_ns=clock_ns,
                                            weight_bits=weight_bits,
                                            activation_bits=activation_bits,
                                            kv_bits=kv_bits,
                                            score_bits=score_bits,
                                            weight_residency=weight_residency,
                                        )
                                    )

    focus_rows = [
        row
        for row in rows
        if row["macs_per_cycle"] == max(macs_per_cycle_list)
        and row["sequence_length"] in {min(sequence_length_list), max(sequence_length_list)}
        and row["kv_bits"] == min(kv_bits_list)
        and row["weight_residency"] == "resident_weights"
    ]
    compact_focus_rows = [_compact_row(row) for row in focus_rows]
    dominant_substage_counts: dict[str, int] = {}
    limiter_counts: dict[str, int] = {}
    for row in rows:
        dominant_substage_counts[row["dominant_substage"]] = dominant_substage_counts.get(row["dominant_substage"], 0) + 1
        for stage in row["stages"]:
            limiter_key = f"{stage['stage']}:{stage['limiter']}"
            limiter_counts[limiter_key] = limiter_counts.get(limiter_key, 0) + 1
    payload = {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_memory_v1",
        "inputs": {
            "sequence_length_list": sequence_length_list,
            "macs_per_cycle_list": macs_per_cycle_list,
            "kv_memory_tier_list": kv_memory_tier_list,
            "kv_sharing_list": kv_sharing_list,
            "kv_bits_list": kv_bits_list,
            "noc_hops_list": noc_hops_list,
            "clock_ns": clock_ns,
            "weight_bits": weight_bits,
            "activation_bits": activation_bits,
            "score_bits": score_bits,
            "vector_ops_per_cycle": vector_ops_per_cycle,
            "weight_bandwidth_bytes_per_cycle": weight_bandwidth_bytes_per_cycle,
            "activation_bandwidth_bytes_per_cycle": activation_bandwidth_bytes_per_cycle,
            "noc_bandwidth_bytes_per_cycle": noc_bandwidth_bytes_per_cycle,
        },
        "assumptions": [
            "This is an analytical single-token decode attention model, not measured RTL.",
            "Q/K/V projection, QK score, softmax, value mix, and attention output projection are separated.",
            "KV read traffic is charged to QK score and value mix; KV write traffic is charged once per token.",
            "KV memory tier bandwidths are planning values: local_sram=1024, shared_sram=256, hbm=64, remote_hbm=32 bytes/cycle.",
            "NoC contention is represented by effective KV bandwidth min(tier_bandwidth, noc_bandwidth / hops) for non-local tiers.",
            "GQA/MQA reduce KV-cache width but not query/output projection width.",
            "streaming_weights charges attention projection weights each token; resident_weights exposes KV and compute pressure.",
        ],
        "detail_policy": {
            "attention_kv_sweep": "compact scalar rows for the decision-focused slice only; full sweep rows are summarized by counts",
            "full_detail": "available only through the optional --detail-out CLI path",
        },
        "sweep_summary": {
            "generated_row_count": len(rows),
            "committed_compact_row_count": len(compact_focus_rows),
            "omitted_full_sweep_row_count": len(rows) - len(compact_focus_rows),
            "dominant_substage_counts": dict(sorted(dominant_substage_counts.items())),
            "stage_limiter_counts": dict(sorted(limiter_counts.items())),
        },
        "attention_kv_sweep": sorted(
            compact_focus_rows,
            key=lambda row: (
                row["label"],
                row["sequence_length"],
                row["kv_memory_tier"],
                row["kv_sharing"],
                row["noc_hops"],
            ),
        ),
        "focus_summary": sorted(
            [
                {
                    "label": row["label"],
                    "sequence_length": row["sequence_length"],
                    "kv_memory_tier": row["kv_memory_tier"],
                    "kv_sharing": row["kv_sharing"],
                    "kv_bits": row["kv_bits"],
                    "noc_hops": row["noc_hops"],
                    "total_latency_us": row["total_latency_us"],
                    "dominant_substage": row["dominant_substage"],
                    "dominant_substage_share": row["dominant_substage_share"],
                    "kv_read_byte_share": row["kv_read_byte_share"],
                    "kv_limited_cycle_share": row["kv_limited_cycle_share"],
                    "effective_kv_bandwidth_bytes_per_cycle": row["effective_kv_bandwidth_bytes_per_cycle"],
                    "arithmetic_intensity": row["attention_arithmetic_intensity_macs_per_byte"],
                }
                for row in focus_rows
            ],
            key=lambda row: (
                row["label"],
                row["sequence_length"],
                row["kv_memory_tier"],
                row["kv_sharing"],
                row["noc_hops"],
            ),
        ),
    }
    if include_detail:
        payload["attention_kv_sweep_detail"] = rows
    return payload


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Attention/KV Memory Breakdown",
        "",
        f"- model: `{payload['model']}`",
        "",
        "## Focus Summary",
        "",
        "| shape | seq | tier | share | bits | hops | total_us | dominant | dom_share | kv_byte_share | kv_cycle_share | eff_kv_B/cyc | intensity |",
        "|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["focus_summary"]:
        lines.append(
            "| {label} | {seq} | {tier} | {share} | {bits} | {hops} | {total} | {dom} | {dom_share} | {kv_bytes} | {kv_cycles} | {eff_bw} | {intensity} |".format(
                label=row["label"],
                seq=row["sequence_length"],
                tier=row["kv_memory_tier"],
                share=row["kv_sharing"],
                bits=row["kv_bits"],
                hops=row["noc_hops"],
                total=row["total_latency_us"],
                dom=row["dominant_substage"],
                dom_share=row["dominant_substage_share"],
                kv_bytes=row["kv_read_byte_share"],
                kv_cycles=row["kv_limited_cycle_share"],
                eff_bw=row["effective_kv_bandwidth_bytes_per_cycle"],
                intensity=row["arithmetic_intensity"],
            )
        )

    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Estimate LLM decoder attention/KV memory hierarchy pressure")
    ap.add_argument("--sequence-length-list", type=_int_list, default=[128, 512, 2048, 8192, 32768])
    ap.add_argument("--macs-per-cycle-list", type=_int_list, default=[8192, 32768, 131072])
    ap.add_argument("--kv-memory-tier-list", type=_str_list, default=["local_sram", "shared_sram", "hbm", "remote_hbm"])
    ap.add_argument("--kv-sharing-list", type=_str_list, default=["mha", "gqa4", "mqa"])
    ap.add_argument("--kv-bits-list", type=_int_list, default=[8, 16])
    ap.add_argument("--noc-hops-list", type=_int_list, default=[1, 2, 4])
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--weight-bits", type=int, default=16)
    ap.add_argument("--activation-bits", type=int, default=16)
    ap.add_argument("--score-bits", type=int, default=16)
    ap.add_argument("--vector-ops-per-cycle", type=int, default=32768)
    ap.add_argument("--weight-bandwidth-bytes-per-cycle", type=float, default=256.0)
    ap.add_argument("--activation-bandwidth-bytes-per-cycle", type=float, default=512.0)
    ap.add_argument("--noc-bandwidth-bytes-per-cycle", type=float, default=256.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--detail-out")
    args = ap.parse_args()

    payload = build_report(
        sequence_length_list=args.sequence_length_list,
        macs_per_cycle_list=args.macs_per_cycle_list,
        kv_memory_tier_list=args.kv_memory_tier_list,
        kv_sharing_list=args.kv_sharing_list,
        kv_bits_list=args.kv_bits_list,
        noc_hops_list=[0, *args.noc_hops_list],
        clock_ns=args.clock_ns,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        score_bits=args.score_bits,
        vector_ops_per_cycle=args.vector_ops_per_cycle,
        weight_bandwidth_bytes_per_cycle=args.weight_bandwidth_bytes_per_cycle,
        activation_bandwidth_bytes_per_cycle=args.activation_bandwidth_bytes_per_cycle,
        noc_bandwidth_bytes_per_cycle=args.noc_bandwidth_bytes_per_cycle,
        include_detail=bool(args.detail_out),
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    committed_payload = dict(payload)
    detail_rows = committed_payload.pop("attention_kv_sweep_detail", None)
    out.write_text(json.dumps(committed_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.detail_out:
        detail_out = Path(args.detail_out)
        detail_out.parent.mkdir(parents=True, exist_ok=True)
        detail_payload = dict(payload)
        detail_payload["attention_kv_sweep_detail"] = detail_rows or []
        detail_out.write_text(json.dumps(detail_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown(out_md, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

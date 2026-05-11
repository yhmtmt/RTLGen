#!/usr/bin/env python3
"""Estimate a coarse decoder-stage latency and traffic breakdown."""

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


def _byte_width(bits: int) -> int:
    return max(1, math.ceil(bits / 8))


def _cycles(*, macs: int, bytes_served: int, macs_per_cycle: int, bandwidth: float) -> int:
    compute_cycles = math.ceil(macs / macs_per_cycle) if macs else 0
    memory_cycles = math.ceil(bytes_served / bandwidth) if bytes_served else 0
    return max(compute_cycles, memory_cycles)


def _stage(
    *,
    name: str,
    macs: int,
    weight_bytes: int,
    activation_bytes: int,
    kv_bytes: int,
    macs_per_cycle: int,
    memory_bandwidth_bytes_per_cycle: float,
    clock_ns: float,
    charge_weights: bool,
) -> JsonDict:
    bytes_served = activation_bytes + kv_bytes + (weight_bytes if charge_weights else 0)
    cycles = _cycles(
        macs=macs,
        bytes_served=bytes_served,
        macs_per_cycle=macs_per_cycle,
        bandwidth=memory_bandwidth_bytes_per_cycle,
    )
    compute_cycles = math.ceil(macs / macs_per_cycle) if macs else 0
    memory_cycles = math.ceil(bytes_served / memory_bandwidth_bytes_per_cycle) if bytes_served else 0
    return {
        "stage": name,
        "macs": macs,
        "weight_bytes": weight_bytes,
        "activation_bytes": activation_bytes,
        "kv_cache_bytes": kv_bytes,
        "charged_bytes": bytes_served,
        "compute_cycles": compute_cycles,
        "memory_cycles": memory_cycles,
        "cycles": cycles,
        "latency_us": round(cycles * clock_ns / 1000.0, 6),
        "limiter": "memory" if memory_cycles >= compute_cycles else "compute",
    }


def _ranker_stage(
    *,
    vocab_size: int,
    ranker_lanes: int,
    ranker_ii_cycles: int,
    logit_bits: int,
    macs_per_cycle: int,
    memory_bandwidth_bytes_per_cycle: float,
    clock_ns: float,
) -> JsonDict:
    # This is a rough standalone bound. Producer-integrated ranker results remain
    # the preferred source when a measured/coupled report is available.
    logit_bytes = vocab_size * _byte_width(logit_bits)
    compare_macs = max(0, vocab_size - 1)
    streaming_cycles = math.ceil(vocab_size / ranker_lanes) * ranker_ii_cycles
    base = _stage(
        name="ranker",
        macs=compare_macs,
        weight_bytes=0,
        activation_bytes=logit_bytes,
        kv_bytes=0,
        macs_per_cycle=macs_per_cycle,
        memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
        clock_ns=clock_ns,
        charge_weights=True,
    )
    cycles = max(base["cycles"], streaming_cycles)
    base.update(
        {
            "cycles": cycles,
            "latency_us": round(cycles * clock_ns / 1000.0, 6),
            "streaming_cycles": streaming_cycles,
            "ranker_lanes": ranker_lanes,
            "ranker_ii_cycles": ranker_ii_cycles,
        }
    )
    return base


def _shape_rows(
    *,
    label: str,
    layers: int,
    hidden_size: int,
    vocab_size: int,
    sequence_length: int,
    ffn_multiplier: int,
    macs_per_cycle: int,
    memory_bandwidth_bytes_per_cycle: float,
    clock_ns: float,
    weight_bits: int,
    activation_bits: int,
    ranker_lanes: int,
    ranker_ii_cycles: int,
    weight_residency: str,
) -> JsonDict:
    weight_b = _byte_width(weight_bits)
    act_b = _byte_width(activation_bits)
    charge_weights = weight_residency == "streaming_weights"

    h = hidden_size
    s = sequence_length
    f = ffn_multiplier

    # Single-token causal decode, per layer:
    # attention = QKV projection + score(QK) + value mix + output projection.
    attn_macs_per_layer = (4 * h * h) + (2 * s * h)
    attn_weight_bytes_per_layer = 4 * h * h * weight_b
    attn_activation_bytes_per_layer = 6 * h * act_b
    attn_kv_bytes_per_layer = ((2 * s * h) + (2 * h)) * act_b

    mlp_macs_per_layer = 2 * f * h * h
    mlp_weight_bytes_per_layer = 2 * f * h * h * weight_b
    mlp_activation_bytes_per_layer = (2 * f * h + h) * act_b

    norm_macs_per_layer = 4 * h
    norm_activation_bytes_per_layer = 4 * h * act_b

    output_macs = vocab_size * h
    output_weight_bytes = vocab_size * h * weight_b
    output_activation_bytes = (vocab_size + h) * act_b

    stages = [
        _stage(
            name="attention",
            macs=layers * attn_macs_per_layer,
            weight_bytes=layers * attn_weight_bytes_per_layer,
            activation_bytes=layers * attn_activation_bytes_per_layer,
            kv_bytes=layers * attn_kv_bytes_per_layer,
            macs_per_cycle=macs_per_cycle,
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="mlp",
            macs=layers * mlp_macs_per_layer,
            weight_bytes=layers * mlp_weight_bytes_per_layer,
            activation_bytes=layers * mlp_activation_bytes_per_layer,
            kv_bytes=0,
            macs_per_cycle=macs_per_cycle,
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="norm_residual",
            macs=layers * norm_macs_per_layer,
            weight_bytes=0,
            activation_bytes=layers * norm_activation_bytes_per_layer,
            kv_bytes=0,
            macs_per_cycle=macs_per_cycle,
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _stage(
            name="output_projection",
            macs=output_macs,
            weight_bytes=output_weight_bytes,
            activation_bytes=output_activation_bytes,
            kv_bytes=0,
            macs_per_cycle=macs_per_cycle,
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
            clock_ns=clock_ns,
            charge_weights=charge_weights,
        ),
        _ranker_stage(
            vocab_size=vocab_size,
            ranker_lanes=ranker_lanes,
            ranker_ii_cycles=ranker_ii_cycles,
            logit_bits=activation_bits,
            macs_per_cycle=macs_per_cycle,
            memory_bandwidth_bytes_per_cycle=memory_bandwidth_bytes_per_cycle,
            clock_ns=clock_ns,
        ),
    ]
    total_cycles = sum(stage["cycles"] for stage in stages)
    for stage in stages:
        stage["cycle_share"] = round(stage["cycles"] / total_cycles, 6) if total_cycles else 0.0
    dominant = max(stages, key=lambda row: row["cycles"])
    return {
        "label": label,
        "layers": layers,
        "hidden_size": hidden_size,
        "vocab_size": vocab_size,
        "sequence_length": sequence_length,
        "ffn_multiplier": ffn_multiplier,
        "macs_per_cycle": macs_per_cycle,
        "memory_bandwidth_bytes_per_cycle": memory_bandwidth_bytes_per_cycle,
        "weight_residency": weight_residency,
        "total_cycles": total_cycles,
        "total_latency_us": round(total_cycles * clock_ns / 1000.0, 6),
        "dominant_stage": dominant["stage"],
        "dominant_stage_share": dominant["cycle_share"],
        "stages": stages,
    }


def build_report(
    *,
    sequence_length_list: list[int],
    macs_per_cycle_list: list[int],
    memory_bandwidth_bytes_per_cycle_list: list[float],
    clock_ns: float,
    weight_bits: int,
    activation_bits: int,
    ranker_lanes: int,
    ranker_ii_cycles: int,
) -> JsonDict:
    shapes = [
        {"label": "gpt2_small", "layers": 12, "hidden_size": 768, "vocab_size": 50257, "ffn_multiplier": 4},
        {"label": "gpt2_medium_proxy", "layers": 24, "hidden_size": 1024, "vocab_size": 50257, "ffn_multiplier": 4},
        {"label": "large_vocab_proxy", "layers": 32, "hidden_size": 2048, "vocab_size": 100000, "ffn_multiplier": 4},
        {"label": "long_context_proxy", "layers": 32, "hidden_size": 4096, "vocab_size": 200000, "ffn_multiplier": 4},
    ]
    rows: list[JsonDict] = []
    for shape in shapes:
        for sequence_length in sequence_length_list:
            for macs_per_cycle in macs_per_cycle_list:
                for bandwidth in memory_bandwidth_bytes_per_cycle_list:
                    for weight_residency in ["streaming_weights", "resident_weights"]:
                        rows.append(
                            _shape_rows(
                                label=shape["label"],
                                layers=shape["layers"],
                                hidden_size=shape["hidden_size"],
                                vocab_size=shape["vocab_size"],
                                sequence_length=sequence_length,
                                ffn_multiplier=shape["ffn_multiplier"],
                                macs_per_cycle=macs_per_cycle,
                                memory_bandwidth_bytes_per_cycle=bandwidth,
                                clock_ns=clock_ns,
                                weight_bits=weight_bits,
                                activation_bits=activation_bits,
                                ranker_lanes=ranker_lanes,
                                ranker_ii_cycles=ranker_ii_cycles,
                                weight_residency=weight_residency,
                            )
                        )

    focus_rows = [
        row
        for row in rows
        if row["macs_per_cycle"] == max(macs_per_cycle_list)
        and row["memory_bandwidth_bytes_per_cycle"] == max(memory_bandwidth_bytes_per_cycle_list)
    ]
    return {
        "version": 0.1,
        "model": "llm_decoder_stage_breakdown_v1",
        "inputs": {
            "sequence_length_list": sequence_length_list,
            "macs_per_cycle_list": macs_per_cycle_list,
            "memory_bandwidth_bytes_per_cycle_list": memory_bandwidth_bytes_per_cycle_list,
            "clock_ns": clock_ns,
            "weight_bits": weight_bits,
            "activation_bits": activation_bits,
            "ranker_lanes": ranker_lanes,
            "ranker_ii_cycles": ranker_ii_cycles,
        },
        "assumptions": [
            "This is a rough stage-serialized single-token decode model, not measured RTL.",
            "Attention includes QKV projection, QK score, value mix, and output projection.",
            "MLP uses a two-projection feed-forward block with ffn_multiplier expansion.",
            "streaming_weights charges decoder and output-projection weights each token.",
            "resident_weights removes weight traffic to expose compute and KV-cache sensitivity.",
            "Ranker is a rough standalone streaming bound; producer-integrated RTL/PPA remains authoritative.",
        ],
        "breakdown_sweep": rows,
        "focus_summary": sorted(
            [
                {
                    "label": row["label"],
                    "sequence_length": row["sequence_length"],
                    "weight_residency": row["weight_residency"],
                    "total_latency_us": row["total_latency_us"],
                    "dominant_stage": row["dominant_stage"],
                    "dominant_stage_share": row["dominant_stage_share"],
                    "stage_shares": {
                        stage["stage"]: stage["cycle_share"] for stage in row["stages"]
                    },
                }
                for row in focus_rows
            ],
            key=lambda row: (row["label"], row["sequence_length"], row["weight_residency"]),
        ),
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Stage Breakdown",
        "",
        f"- model: `{payload['model']}`",
        "",
        "## Focus Summary",
        "",
        "| shape | seq | weight model | total_us | dominant | share | attention | mlp | output_projection | ranker |",
        "|---|---:|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["focus_summary"]:
        shares = row["stage_shares"]
        lines.append(
            "| {label} | {seq} | {weight} | {total} | {dom} | {share} | {attn} | {mlp} | {out} | {ranker} |".format(
                label=row["label"],
                seq=row["sequence_length"],
                weight=row["weight_residency"],
                total=row["total_latency_us"],
                dom=row["dominant_stage"],
                share=row["dominant_stage_share"],
                attn=shares.get("attention", 0.0),
                mlp=shares.get("mlp", 0.0),
                out=shares.get("output_projection", 0.0),
                ranker=shares.get("ranker", 0.0),
            )
        )

    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Estimate coarse LLM decoder stage breakdown")
    ap.add_argument("--sequence-length-list", type=_int_list, default=[128, 512, 2048, 8192])
    ap.add_argument("--macs-per-cycle-list", type=_int_list, default=[8192, 32768])
    ap.add_argument("--memory-bandwidth-bytes-per-cycle-list", type=_float_list, default=[64.0, 256.0])
    ap.add_argument("--clock-ns", type=float, default=1.0)
    ap.add_argument("--weight-bits", type=int, default=16)
    ap.add_argument("--activation-bits", type=int, default=16)
    ap.add_argument("--ranker-lanes", type=int, default=64)
    ap.add_argument("--ranker-ii-cycles", type=int, default=384)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_report(
        sequence_length_list=args.sequence_length_list,
        macs_per_cycle_list=args.macs_per_cycle_list,
        memory_bandwidth_bytes_per_cycle_list=args.memory_bandwidth_bytes_per_cycle_list,
        clock_ns=args.clock_ns,
        weight_bits=args.weight_bits,
        activation_bits=args.activation_bits,
        ranker_lanes=args.ranker_lanes,
        ranker_ii_cycles=args.ranker_ii_cycles,
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

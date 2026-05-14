#!/usr/bin/env python3
"""Synthesize decoder stage, attention/KV, and producer/ranker frontier reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]


def _load_json(path: str) -> JsonDict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _stage_component_us(row: JsonDict, stage_name: str) -> float:
    for stage in row.get("stages", []):
        if stage.get("stage") == stage_name:
            return float(stage.get("latency_us", 0.0) or 0.0)
    shares = row.get("stage_shares", {})
    return float(row.get("total_latency_us", 0.0) or 0.0) * float(shares.get(stage_name, 0.0) or 0.0)


def _best_attention_by_label_seq(payload: JsonDict) -> dict[tuple[str, int], JsonDict]:
    best: dict[tuple[str, int], JsonDict] = {}
    for row in payload.get("focus_summary", []):
        key = (str(row.get("label", "")), int(row.get("sequence_length", 0) or 0))
        if not key[0] or key[1] <= 0:
            continue
        current = best.get(key)
        if current is None or float(row.get("total_latency_us", 0.0)) < float(current.get("total_latency_us", 0.0)):
            best[key] = row
    return best


def _best_producer_by_shape(payload: JsonDict) -> dict[tuple[int, int], JsonDict]:
    best: dict[tuple[int, int], JsonDict] = {}
    rows = payload.get("coupled_ranker_sweep") or payload.get("producer_service_sweep") or []
    for row in rows:
        if row.get("ranker_fifo_capacity_ok") is False:
            continue
        key = (int(row.get("hidden_size", 0) or 0), int(row.get("vocab_size", 0) or 0))
        if key[0] <= 0 or key[1] <= 0:
            continue
        current = best.get(key)
        latency = float(
            row.get("coupled_latency_us_per_token")
            or row.get("producer_latency_us_per_token")
            or 0.0
        )
        current_latency = float(
            current.get("coupled_latency_us_per_token")
            or current.get("producer_latency_us_per_token")
            or 0.0
        ) if current else 0.0
        if current is None or latency < current_latency:
            best[key] = row
    return best


def _dominant_component(components: dict[str, float]) -> tuple[str, float]:
    if not components:
        return "unknown", 0.0
    name, value = max(components.items(), key=lambda item: item[1])
    total = sum(max(v, 0.0) for v in components.values())
    share = value / total if total > 0.0 else 0.0
    return name, round(share, 6)


def build_report(*, stage_breakdown: JsonDict, attention_kv: JsonDict, producer_ranker: JsonDict) -> JsonDict:
    attention_best = _best_attention_by_label_seq(attention_kv)
    producer_best = _best_producer_by_shape(producer_ranker)
    rows: list[JsonDict] = []

    for row in stage_breakdown.get("breakdown_sweep", []):
        if row.get("weight_residency") != "resident_weights":
            continue
        label = str(row.get("label", ""))
        sequence_length = int(row.get("sequence_length", 0) or 0)
        hidden_size = int(row.get("hidden_size", 0) or 0)
        vocab_size = int(row.get("vocab_size", 0) or 0)
        if not label or sequence_length <= 0:
            continue
        attention = attention_best.get((label, sequence_length))
        producer = producer_best.get((hidden_size, vocab_size))
        if attention is None or producer is None:
            continue
        producer_us = float(
            producer.get("coupled_latency_us_per_token")
            or producer.get("producer_latency_us_per_token")
            or 0.0
        )
        components = {
            "attention_kv_best": float(attention.get("total_latency_us", 0.0) or 0.0),
            "mlp_resident": _stage_component_us(row, "mlp"),
            "output_projection_producer_ranker": producer_us,
            "norm_residual": _stage_component_us(row, "norm_residual"),
        }
        dominant, dominant_share = _dominant_component(components)
        rows.append(
            {
                "label": label,
                "sequence_length": sequence_length,
                "hidden_size": hidden_size,
                "vocab_size": vocab_size,
                "macs_per_cycle": row.get("macs_per_cycle"),
                "memory_bandwidth_bytes_per_cycle": row.get("memory_bandwidth_bytes_per_cycle"),
                "dominant_component": dominant,
                "dominant_component_share": dominant_share,
                "component_latency_us": {key: round(value, 6) for key, value in components.items()},
                "attention_choice": {
                    "kv_memory_tier": attention.get("kv_memory_tier"),
                    "kv_sharing": attention.get("kv_sharing"),
                    "kv_bits": attention.get("kv_bits"),
                    "noc_hops": attention.get("noc_hops"),
                    "dominant_substage": attention.get("dominant_substage"),
                    "kv_limited_cycle_share": attention.get("kv_limited_cycle_share"),
                },
                "producer_choice": {
                    "producer_lanes": producer.get("producer_lanes"),
                    "top_k": producer.get("top_k"),
                    "memory_share": producer.get("memory_share"),
                    "producer_ii_cycles": producer.get("producer_ii_cycles"),
                    "service_limiter": producer.get("service_limiter"),
                    "traffic_reduction_vs_materialized": producer.get("ranker_traffic_reduction_vs_materialized"),
                },
            }
        )

    focus_rows = [
        row
        for row in rows
        if row["macs_per_cycle"] == max([r["macs_per_cycle"] for r in rows], default=0)
        and row["memory_bandwidth_bytes_per_cycle"] == max(
            [r["memory_bandwidth_bytes_per_cycle"] for r in rows], default=0
        )
    ]
    dominant_counts: dict[str, int] = {}
    for row in rows:
        dominant_counts[row["dominant_component"]] = dominant_counts.get(row["dominant_component"], 0) + 1

    tile_frontier = attention_kv.get("measured_attention_kv_tile_frontier", {})
    return {
        "version": 0.1,
        "model": "llm_decoder_frontier_synthesis_v1",
        "inputs": {
            "stage_breakdown_model": stage_breakdown.get("model"),
            "attention_kv_model": attention_kv.get("model"),
            "producer_ranker_model": producer_ranker.get("model"),
            "producer_control_boundary": producer_ranker.get("producer_control_boundary"),
        },
        "measured_attention_kv_tile_summary": tile_frontier.get("scaling_summary", {}),
        "dominant_component_counts": dominant_counts,
        "frontier_rows": rows,
        "focus_summary": sorted(
            focus_rows,
            key=lambda row: (row["label"], row["sequence_length"], row["dominant_component"]),
        ),
        "assumptions": [
            "This is a synthesis of existing analytical reports, not a new RTL measurement.",
            "Attention/KV uses the best latency row per shape and sequence from the calibrated attention/KV report.",
            "Producer/ranker uses the best FIFO-valid coupled row per hidden/vocab shape.",
            "MLP and norm are resident-weight estimates from the whole-decoder stage breakdown.",
            "Use this report to choose the next measured RTL frontier, not as final PPA accounting.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Frontier Synthesis",
        "",
        f"- model: `{payload['model']}`",
        "",
        "## Focus Summary",
        "",
        "| shape | seq | dominant | share | attention_us | mlp_us | producer_ranker_us | attention choice | producer choice |",
        "|---|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["focus_summary"]:
        comp = row["component_latency_us"]
        attn = row["attention_choice"]
        prod = row["producer_choice"]
        lines.append(
            "| {label} | {seq} | {dom} | {share} | {attn_us} | {mlp_us} | {prod_us} | {attn_choice} | {prod_choice} |".format(
                label=row["label"],
                seq=row["sequence_length"],
                dom=row["dominant_component"],
                share=row["dominant_component_share"],
                attn_us=comp["attention_kv_best"],
                mlp_us=comp["mlp_resident"],
                prod_us=comp["output_projection_producer_ranker"],
                attn_choice=(
                    f"{attn['kv_memory_tier']}/{attn['kv_sharing']}/"
                    f"kv{attn['kv_bits']}/hops{attn['noc_hops']}"
                ),
                prod_choice=(
                    f"w{prod['producer_lanes']}/k{prod['top_k']}/"
                    f"share{prod['memory_share']}/ii{prod['producer_ii_cycles']}"
                ),
            )
        )

    lines.extend(["", "## Measured Attention/KV Tile Summary", ""])
    for key, value in payload["measured_attention_kv_tile_summary"].items():
        lines.append(f"- {key}: `{value}`")
    control_boundary = payload.get("inputs", {}).get("producer_control_boundary")
    if control_boundary:
        lines.extend(
            [
                "",
                "## Producer Control Boundary",
                "",
                f"- decision: `{control_boundary.get('decision')}`",
                f"- guard_variant: `{control_boundary.get('guard_variant')}`",
                f"- synthesis_status: `{control_boundary.get('synthesis_status')}`",
                f"- synthesis_elapsed_seconds: `{control_boundary.get('synthesis_elapsed_seconds')}`",
                f"- reg_bits_est: `{control_boundary.get('reg_bits_est')}`",
                f"- wire_bits_est: `{control_boundary.get('wire_bits_est')}`",
            ]
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize LLM decoder frontier reports")
    ap.add_argument("--stage-breakdown", required=True)
    ap.add_argument("--attention-kv-memory", required=True)
    ap.add_argument("--producer-ranker-coupled", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_report(
        stage_breakdown=_load_json(args.stage_breakdown),
        attention_kv=_load_json(args.attention_kv_memory),
        producer_ranker=_load_json(args.producer_ranker_coupled),
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

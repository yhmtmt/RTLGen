#!/usr/bin/env python3
"""Build a measured SRAM profile target for Llama7B decoder attention."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.synth.aggregate_sram_metrics import summarize_metrics  # noqa: E402


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class BufferSpec:
    name: str
    scope: str
    logical_bytes: int
    word_bits: int
    banks: int
    depth: int
    width_bits: int
    access_role: str


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def _next_power_of_two(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (value - 1).bit_length()


def _round_sram_shape(*, logical_bytes: int, preferred_word_bits: int, max_bank_width_bits: int) -> tuple[int, int, int]:
    word_bits = min(preferred_word_bits, max_bank_width_bits)
    word_bytes = max(1, word_bits // 8)
    words = _ceil_div(logical_bytes, word_bytes)
    depth = _next_power_of_two(words)
    return 1, depth, word_bits


def build_buffer_specs(
    *,
    tile_tokens: int,
    hidden_size: int,
    attention_heads: int,
    kv_heads: int,
    score_bits: int,
    softmax_weight_bits: int,
    kv_bits: int,
    accumulator_bits: int,
    output_bits: int,
    max_bank_width_bits: int,
) -> list[BufferSpec]:
    head_dim = hidden_size // attention_heads
    per_token_kv_bits = kv_heads * head_dim * kv_bits
    logical_specs = [
        (
            "score_tile_buffer",
            "tile-local score buffering before softmax",
            tile_tokens * attention_heads * score_bits // 8,
            attention_heads * score_bits,
            "read_write",
        ),
        (
            "softmax_weight_buffer",
            "normalized softmax weights consumed by value accumulation",
            tile_tokens * attention_heads * softmax_weight_bits // 8,
            attention_heads * softmax_weight_bits,
            "read_write",
        ),
        (
            "kv_tile_read_buffer",
            "tile-local K and V read staging for the selected KV sharing",
            2 * tile_tokens * per_token_kv_bits // 8,
            min(max_bank_width_bits, per_token_kv_bits),
            "read",
        ),
        (
            "partial_value_buffer",
            "per-head partial value vector before cross-tile reduction",
            hidden_size * accumulator_bits // 8,
            max_bank_width_bits,
            "read_write",
        ),
        (
            "result_writeback_buffer",
            "final attention output writeback staging",
            hidden_size * output_bits // 8,
            max_bank_width_bits,
            "write",
        ),
        (
            "softmax_stats_buffer",
            "per-head max and sum statistics for stable normalization",
            attention_heads * 2 * accumulator_bits // 8,
            max_bank_width_bits,
            "read_write",
        ),
    ]

    buffers: list[BufferSpec] = []
    for name, scope, logical_bytes, preferred_word_bits, access_role in logical_specs:
        banks, depth, width_bits = _round_sram_shape(
            logical_bytes=max(1, int(logical_bytes)),
            preferred_word_bits=max(8, int(preferred_word_bits)),
            max_bank_width_bits=max_bank_width_bits,
        )
        buffers.append(
            BufferSpec(
                name=name,
                scope=scope,
                logical_bytes=int(logical_bytes),
                word_bits=int(preferred_word_bits),
                banks=banks,
                depth=depth,
                width_bits=width_bits,
                access_role=access_role,
            )
        )
    return buffers


def arch_payload(*, buffers: list[BufferSpec], pdk: str, tech_node_nm: int) -> JsonDict:
    return {
        "schema_version": "0.2-draft",
        "platform": {
            "target_pdk": pdk,
            "tech_node_nm": tech_node_nm,
        },
        "memory": {
            "instances": [
                {
                    "name": buffer.name,
                    "depth": buffer.depth,
                    "width": buffer.width_bits,
                    "banks": buffer.banks,
                    "port": "1r1w",
                }
                for buffer in buffers
            ]
        },
    }


def _write_report(payload: JsonDict, report_path: Path) -> None:
    lines = [
        "# Llama7B Attention SRAM Profile",
        "",
        "## Logical Buffers",
        "",
        "| buffer | scope | logical bytes | SRAM shape | role |",
        "|---|---|---:|---|---|",
    ]
    for buffer in payload["buffers"]:
        shape = f"{buffer['banks']} x depth {buffer['depth']} x width {buffer['width_bits']}"
        lines.append(
            f"| {buffer['name']} | {buffer['scope']} | {buffer['logical_bytes']} | {shape} | {buffer['access_role']} |"
        )
    lines.extend(
        [
            "",
            "## Totals",
            "",
            f"- logical_buffer_bytes: `{payload['totals']['logical_buffer_bytes']}`",
            f"- allocated_sram_bytes: `{payload['totals']['allocated_sram_bytes']}`",
            f"- capacity_overhead: `{payload['totals']['capacity_overhead']}`",
        ]
    )
    metrics = payload.get("sram_metrics_summary")
    if metrics:
        lines.extend(
            [
                "",
                "## CACTI Summary",
                "",
                f"- total_area_um2: `{metrics.get('total_area_um2')}`",
                f"- max_access_time_ns: `{metrics.get('max_access_time_ns')}`",
                f"- total_read_energy_pj: `{metrics.get('total_read_energy_pj')}`",
                f"- total_write_energy_pj: `{metrics.get('total_write_energy_pj')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This profile measures tile-local buffering only; the full 131k-token KV cache residency remains a higher-level memory-capacity decision.",
            "- SRAM shapes are banked logical targets for CACTI and are not a placed SRAM macro floorplan.",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_profile_payload(
    *,
    buffers: list[BufferSpec],
    args: argparse.Namespace,
    sram_metrics_summary: JsonDict | None,
    sram_metrics_json: str | None,
) -> JsonDict:
    allocated_bytes = sum(buffer.banks * buffer.depth * buffer.width_bits // 8 for buffer in buffers)
    logical_bytes = sum(buffer.logical_bytes for buffer in buffers)
    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_sram_profile",
        "parameters": {
            "sequence_length": args.sequence_length,
            "tile_tokens": args.tile_tokens,
            "hidden_size": args.hidden_size,
            "attention_heads": args.attention_heads,
            "kv_heads": args.kv_heads,
            "head_dim": args.hidden_size // args.attention_heads,
            "score_bits": args.score_bits,
            "softmax_weight_bits": args.softmax_weight_bits,
            "kv_bits": args.kv_bits,
            "accumulator_bits": args.accumulator_bits,
            "output_bits": args.output_bits,
            "max_bank_width_bits": args.max_bank_width_bits,
        },
        "buffers": [asdict(buffer) for buffer in buffers],
        "totals": {
            "logical_buffer_bytes": logical_bytes,
            "allocated_sram_bytes": allocated_bytes,
            "capacity_overhead": round(allocated_bytes / logical_bytes, 6) if logical_bytes else None,
        },
        "sram_metrics_json": sram_metrics_json,
        "sram_metrics_summary": sram_metrics_summary,
        "remaining_abstractions": [
            "CACTI SRAM estimates are macro-level access/energy estimates, not placed SRAM compiler macros.",
            "The full KV cache capacity and HBM service are not included in this tile-local profile.",
            "NoC arbitration and contention are measured by a separate closure item.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--arch-out", required=True, type=Path)
    parser.add_argument("--sram-id", default="llama7b_attention_tile_buffers_v1")
    parser.add_argument("--sequence-length", type=int, default=131072)
    parser.add_argument("--tile-tokens", type=int, default=512)
    parser.add_argument("--hidden-size", type=int, default=4096)
    parser.add_argument("--attention-heads", type=int, default=32)
    parser.add_argument("--kv-heads", type=int, default=4)
    parser.add_argument("--score-bits", type=int, default=16)
    parser.add_argument("--softmax-weight-bits", type=int, default=16)
    parser.add_argument("--kv-bits", type=int, default=8)
    parser.add_argument("--accumulator-bits", type=int, default=32)
    parser.add_argument("--output-bits", type=int, default=16)
    parser.add_argument("--max-bank-width-bits", type=int, default=256)
    parser.add_argument("--pdk", default="nangate45")
    parser.add_argument("--tech-node-nm", type=int, default=45)
    parser.add_argument("--run-cacti", action="store_true")
    args = parser.parse_args()

    if args.hidden_size % args.attention_heads != 0:
        raise SystemExit("--hidden-size must be divisible by --attention-heads")
    if args.max_bank_width_bits % 8 != 0:
        raise SystemExit("--max-bank-width-bits must be a multiple of 8")

    buffers = build_buffer_specs(
        tile_tokens=args.tile_tokens,
        hidden_size=args.hidden_size,
        attention_heads=args.attention_heads,
        kv_heads=args.kv_heads,
        score_bits=args.score_bits,
        softmax_weight_bits=args.softmax_weight_bits,
        kv_bits=args.kv_bits,
        accumulator_bits=args.accumulator_bits,
        output_bits=args.output_bits,
        max_bank_width_bits=args.max_bank_width_bits,
    )

    args.arch_out.parent.mkdir(parents=True, exist_ok=True)
    args.arch_out.write_text(yaml.safe_dump(arch_payload(buffers=buffers, pdk=args.pdk, tech_node_nm=args.tech_node_nm), sort_keys=False), encoding="utf-8")

    sram_metrics_summary = None
    sram_metrics_json = None
    if args.run_cacti:
        subprocess.run(
            [
                sys.executable,
                "npu/synth/sram_ppa.py",
                str(args.arch_out),
                "--id",
                args.sram_id,
            ],
            cwd=_REPO_ROOT,
            check=True,
        )
        metrics_path = Path("runs/designs/sram") / args.sram_id / "sram_metrics.json"
        sram_metrics_json = str(metrics_path)
        sram_metrics_summary = summarize_metrics(_REPO_ROOT / metrics_path)
        summary_path = _REPO_ROOT / "runs/designs/sram" / args.sram_id / "sram_metrics_summary.json"
        summary_path.write_text(json.dumps(sram_metrics_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = build_profile_payload(
        buffers=buffers,
        args=args,
        sram_metrics_summary=sram_metrics_summary,
        sram_metrics_json=sram_metrics_json,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

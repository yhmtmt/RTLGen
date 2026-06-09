#!/usr/bin/env python3
"""Measure chunked local SRAM capacity needed by the selected Llama7B frontier."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.synth.aggregate_sram_metrics import summarize_metrics  # noqa: E402


JsonDict = dict[str, Any]


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _next_power_of_two(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (value - 1).bit_length()


def _largest_power_of_two_leq(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (value.bit_length() - 1)


def _chunk_capacity(*, logical_bytes: int, min_chunk_bytes: int, max_chunk_bytes: int) -> list[int]:
    if logical_bytes <= 0:
        raise ValueError("logical_bytes must be positive")
    remaining = logical_bytes
    chunks: list[int] = []
    while remaining > 0:
        if remaining <= min_chunk_bytes:
            chunks.append(max(min_chunk_bytes, _next_power_of_two(remaining)))
            break
        chunk = min(max_chunk_bytes, _largest_power_of_two_leq(remaining))
        chunk = max(chunk, min_chunk_bytes)
        chunks.append(chunk)
        remaining -= chunk
    return chunks


def _arch_payload(*, chunks: list[int], width_bits: int, pdk: str, tech_node_nm: int) -> JsonDict:
    word_bytes = width_bits // 8
    return {
        "schema_version": "0.2-draft",
        "platform": {
            "target_pdk": pdk,
            "tech_node_nm": tech_node_nm,
        },
        "memory": {
            "instances": [
                {
                    "name": f"local_capacity_chunk_{idx:02d}_{chunk_bytes // 1024}kib",
                    "depth": chunk_bytes // word_bytes,
                    "width": width_bits,
                    "banks": 1,
                    "port": "1r1w",
                }
                for idx, chunk_bytes in enumerate(chunks)
            ]
        },
    }


def _build_profile(
    *,
    source: JsonDict,
    sram_metrics_summary: JsonDict | None,
    sram_metrics_json: str | None,
    chunks: list[int],
    width_bits: int,
    min_chunk_bytes: int,
    max_chunk_bytes: int,
) -> JsonDict:
    best = source.get("best", source)
    active_clusters = int(best["active_clusters"])
    local_capacity_bytes_per_cluster = int(best["local_capacity_bytes_per_cluster"])
    allocated_bytes_per_cluster = sum(chunks)
    sram_budget_area_um2 = float(best["die_area_mm2"]) * 1_000_000.0 * float(best["sram_area_fraction"])

    per_cluster_summary = sram_metrics_summary or {}
    total_area_um2 = float(per_cluster_summary.get("total_area_um2", 0.0)) * active_clusters
    total_read_energy_pj = float(per_cluster_summary.get("total_read_energy_pj", 0.0)) * active_clusters
    total_write_energy_pj = float(per_cluster_summary.get("total_write_energy_pj", 0.0)) * active_clusters
    return {
        "version": 1,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_local_sram_capacity",
        "source_item": "l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1",
        "selected_frontier": {
            "latency_us": best["latency_us"],
            "active_clusters": active_clusters,
            "cluster_count": best["cluster_count"],
            "bank_count": best["bank_count"],
            "local_sram_fraction": best["local_sram_fraction"],
            "sram_area_fraction": best["sram_area_fraction"],
            "local_capacity_bytes_per_cluster": local_capacity_bytes_per_cluster,
            "local_capacity_mib_total": best.get("local_capacity_mib"),
            "die_area_mm2": best["die_area_mm2"],
        },
        "chunking": {
            "width_bits": width_bits,
            "word_bytes": width_bits // 8,
            "min_chunk_bytes": min_chunk_bytes,
            "max_chunk_bytes": max_chunk_bytes,
            "chunks_bytes": chunks,
            "chunk_count_per_cluster": len(chunks),
            "allocated_bytes_per_cluster": allocated_bytes_per_cluster,
            "capacity_overhead": round(allocated_bytes_per_cluster / local_capacity_bytes_per_cluster, 6),
            "allocated_bytes_all_clusters": allocated_bytes_per_cluster * active_clusters,
        },
        "sram_metrics_json": sram_metrics_json,
        "per_cluster_sram_metrics_summary": per_cluster_summary,
        "all_cluster_sram_metrics_summary": {
            "total_area_um2": total_area_um2,
            "total_read_energy_pj": total_read_energy_pj,
            "total_write_energy_pj": total_write_energy_pj,
            "max_access_time_ns": per_cluster_summary.get("max_access_time_ns"),
            "active_clusters": active_clusters,
        },
        "budget_check": {
            "sram_budget_area_um2": sram_budget_area_um2,
            "total_area_um2": total_area_um2,
            "area_fraction_of_sram_budget": round(total_area_um2 / max(1.0, sram_budget_area_um2), 6),
            "fits_sram_budget": total_area_um2 <= sram_budget_area_um2 if total_area_um2 else None,
        },
        "remaining_abstractions": [
            "CACTI estimates are macro-level SRAM access/energy estimates, not a placed SRAM compiler floorplan.",
            "The profile models local-capacity SRAM chunks only; HBM/DRAM service remains separate.",
            "NoC arbitration and endpoint/router PPA are measured by separate closure items.",
        ],
    }


def _write_report(payload: JsonDict, report: Path) -> None:
    selected = payload["selected_frontier"]
    chunking = payload["chunking"]
    budget = payload["budget_check"]
    lines = [
        "# Llama7B Local SRAM Capacity Profile",
        "",
        "## Selected Frontier",
        f"- active_clusters: `{selected['active_clusters']}`",
        f"- local_capacity_bytes_per_cluster: `{selected['local_capacity_bytes_per_cluster']}`",
        f"- local_sram_fraction: `{selected['local_sram_fraction']}`",
        f"- sram_area_fraction: `{selected['sram_area_fraction']}`",
        "",
        "## Chunking",
        f"- width_bits: `{chunking['width_bits']}`",
        f"- chunk_count_per_cluster: `{chunking['chunk_count_per_cluster']}`",
        f"- allocated_bytes_per_cluster: `{chunking['allocated_bytes_per_cluster']}`",
        f"- capacity_overhead: `{chunking['capacity_overhead']}`",
        f"- chunks_bytes: `{chunking['chunks_bytes']}`",
        "",
        "## Budget",
        f"- total_area_um2: `{budget['total_area_um2']}`",
        f"- sram_budget_area_um2: `{budget['sram_budget_area_um2']}`",
        f"- area_fraction_of_sram_budget: `{budget['area_fraction_of_sram_budget']}`",
        f"- fits_sram_budget: `{budget['fits_sram_budget']}`",
        "",
        "## Remaining Abstractions",
    ]
    for item in payload["remaining_abstractions"]:
        lines.append(f"- {item}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--arch-out", type=Path, required=True)
    parser.add_argument("--sram-id", default="llama7b_attention_local_capacity_v1")
    parser.add_argument("--width-bits", type=int, default=1024)
    parser.add_argument("--min-chunk-bytes", type=int, default=16 * 1024)
    parser.add_argument("--max-chunk-bytes", type=int, default=16 * 1024 * 1024)
    parser.add_argument("--pdk", default="nangate45")
    parser.add_argument("--tech-node-nm", type=int, default=45)
    parser.add_argument("--run-cacti", action="store_true")
    args = parser.parse_args()

    if args.width_bits % 8 != 0:
        raise SystemExit("--width-bits must be a multiple of 8")
    source = _load_json(args.source_json)
    best = source.get("best", source)
    local_capacity_bytes_per_cluster = int(best["local_capacity_bytes_per_cluster"])
    chunks = _chunk_capacity(
        logical_bytes=local_capacity_bytes_per_cluster,
        min_chunk_bytes=args.min_chunk_bytes,
        max_chunk_bytes=args.max_chunk_bytes,
    )
    args.arch_out.parent.mkdir(parents=True, exist_ok=True)
    args.arch_out.write_text(
        yaml.safe_dump(
            _arch_payload(chunks=chunks, width_bits=args.width_bits, pdk=args.pdk, tech_node_nm=args.tech_node_nm),
            sort_keys=False,
        ),
        encoding="utf-8",
    )

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

    payload = _build_profile(
        source=source,
        sram_metrics_summary=sram_metrics_summary,
        sram_metrics_json=sram_metrics_json,
        chunks=chunks,
        width_bits=args.width_bits,
        min_chunk_bytes=args.min_chunk_bytes,
        max_chunk_bytes=args.max_chunk_bytes,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

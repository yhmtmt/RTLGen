#!/usr/bin/env python3
"""Estimate Llama7B attention/KV with measured NPU compute PPA substitution."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.estimate_llm_decoder_attention_kv_physical_hbm_frontier import _shape_row

JsonDict = dict[str, Any]


_NM_RE = re.compile(r"_nm(\d+)_")
def _float_list(value: str) -> list[float]:
    items = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated floats")
    return items


def _int_list(value: str) -> list[int]:
    items = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not items:
        raise argparse.ArgumentTypeError("expected comma-separated integers")
    return items


def _style_from_tag(tag: str) -> str:
    if "flat_nomacro" in tag:
        return "flat"
    if "hier_macro" in tag:
        return "hier"
    return "unknown"


def _load_num_modules(config_path: Path) -> tuple[int, int, int]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    gemm = ((payload.get("compute") or {}).get("gemm") or {})
    vec = ((payload.get("compute") or {}).get("vec") or {})
    return (
        int(gemm.get("num_modules", 1)),
        int(gemm.get("lanes_per_module", gemm.get("lanes", 1))),
        int(vec.get("lanes", 1)),
    )


def _load_legacy_npu_compute_candidates(*, repo_root: Path, tag_substring: str) -> list[JsonDict]:
    candidates: list[JsonDict] = []
    for metrics_path in sorted((repo_root / "runs/designs/npu_blocks").glob("npu_fp16_cpp_nm*_cmp/metrics.csv")):
        match = _NM_RE.search(str(metrics_path))
        if not match:
            continue
        nm = int(match.group(1))
        config_path = metrics_path.parent / f"config_nm{nm}.json"
        if not config_path.exists():
            continue
        num_modules, lanes_per_module, vec_lanes = _load_num_modules(config_path)
        with metrics_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                tag = str(row.get("tag", ""))
                if tag_substring not in tag:
                    continue
                if str(row.get("status", "")).strip() != "ok":
                    continue
                delay_ns = float(row["critical_path_ns"])
                instance_area_um2 = float(row["instance_area_um2"])
                total_power_mw = float(row["total_power_mw"])
                candidates.append(
                    {
                        "compute_arch": f"nm{nm}_{_style_from_tag(tag)}",
                        "num_modules": num_modules,
                        "lanes_per_module": lanes_per_module,
                        "block_macs_per_cycle": num_modules * lanes_per_module,
                        "block_vec_lanes": vec_lanes,
                        "block_clock_ns": delay_ns,
                        "block_area_um2": instance_area_um2,
                        "block_power_mw": total_power_mw,
                        "metrics_csv": str(metrics_path.relative_to(repo_root)),
                        "metrics_tag": tag,
                        "metrics_param_hash": row.get("param_hash", ""),
                        "compute_source": "legacy_npu_block",
                    }
                )
    return candidates


def _load_dense_tile_shape(config_path: Path) -> tuple[str, int, int, int, int]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    tile = payload.get("dense_gemm_tile") or {}
    return (
        str(tile.get("precision", "fp16")).lower(),
        int(tile.get("array_m", 1)),
        int(tile.get("array_n", 1)),
        int(tile.get("k_unroll", 1)),
        int(tile.get("pipeline_stages", 1)),
    )


def _load_dense_gemm_tile_candidates(*, repo_root: Path, tag_substring: str) -> list[JsonDict]:
    candidates: list[JsonDict] = []
    design_metric_paths = sorted((repo_root / "runs/designs/npu_blocks").glob("npu_dense_gemm_tile_*/metrics.csv"))
    campaign_metric_paths = sorted((repo_root / "runs/campaigns" / "npu").glob("dense_gemm_tile_*/*/metrics.csv"))
    for metrics_path in design_metric_paths + campaign_metric_paths:
        design_name = metrics_path.parent.name
        config_path = repo_root / "runs" / "designs" / "npu_blocks" / design_name / "config.json"
        if not config_path.exists():
            continue
        precision, array_m, array_n, k_unroll, pipeline_stages = _load_dense_tile_shape(config_path)
        block_macs_per_cycle = array_m * array_n * k_unroll
        if precision == "fp16":
            compute_arch = f"dense_gemm_{array_m}x{array_n}_k{k_unroll}_p{pipeline_stages}"
        else:
            compute_arch = f"dense_gemm_{precision}_{array_m}x{array_n}_k{k_unroll}_p{pipeline_stages}"
        with metrics_path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                tag = str(row.get("tag", ""))
                if tag_substring and tag_substring not in tag:
                    continue
                if str(row.get("status", "")).strip() != "ok":
                    continue
                delay_ns = float(row["critical_path_ns"])
                instance_area_um2 = float(row["instance_area_um2"])
                total_power_mw = float(row["total_power_mw"])
                candidates.append(
                    {
                        "compute_arch": compute_arch,
                        "compute_precision": precision,
                        "num_modules": 1,
                        "lanes_per_module": block_macs_per_cycle,
                        "block_macs_per_cycle": block_macs_per_cycle,
                        "block_vec_lanes": 0,
                        "block_clock_ns": delay_ns,
                        "block_area_um2": instance_area_um2,
                        "block_power_mw": total_power_mw,
                        "metrics_csv": str(metrics_path.relative_to(repo_root)),
                        "metrics_tag": tag,
                        "metrics_param_hash": row.get("param_hash", ""),
                        "compute_source": "dense_gemm_tile",
                        "dense_array_m": array_m,
                        "dense_array_n": array_n,
                        "dense_k_unroll": k_unroll,
                        "dense_pipeline_stages": pipeline_stages,
                    }
                )
    return candidates


def _load_compute_candidates(*, repo_root: Path, tag_substring: str, compute_source: str) -> list[JsonDict]:
    source = compute_source.strip()
    candidates: list[JsonDict] = []
    if source in {"legacy_npu_block", "all"}:
        candidates.extend(_load_legacy_npu_compute_candidates(repo_root=repo_root, tag_substring=tag_substring))
    if source in {"dense_gemm_tile", "all"}:
        candidates.extend(_load_dense_gemm_tile_candidates(repo_root=repo_root, tag_substring=tag_substring))
    if source not in {"legacy_npu_block", "dense_gemm_tile", "all"}:
        raise RuntimeError(f"unsupported compute source: {compute_source!r}")
    if not candidates:
        raise RuntimeError(
            f"no measured compute candidates found with source {compute_source!r} "
            f"and tag substring {tag_substring!r}"
        )
    return candidates


def _best_by(rows: list[JsonDict], keys: tuple[str, ...]) -> list[JsonDict]:
    best: dict[tuple[Any, ...], JsonDict] = {}
    for row in rows:
        key = tuple(row[name] for name in keys)
        current = best.get(key)
        if current is None or row["latency_us"] < current["latency_us"]:
            best[key] = row
    return sorted(best.values(), key=lambda row: tuple(row[name] for name in keys) + (row["latency_us"],))


def _shape_with_compute(
    *,
    candidate: JsonDict,
    die_area_mm2: float,
    sram_area_fraction: float,
    logic_area_fraction: float,
    reserved_area_fraction: float,
    vector_ops_per_mac: float,
    sequence_length: int,
    usable_sram_fraction: float,
    local_sram_fraction: float,
    tile_tokens: int,
    bank_count: int,
) -> JsonDict | None:
    if sram_area_fraction + logic_area_fraction + reserved_area_fraction > 1.0:
        return None
    compute_budget_um2 = die_area_mm2 * 1_000_000.0 * logic_area_fraction
    replica_count = int(compute_budget_um2 // candidate["block_area_um2"])
    if replica_count < 1:
        return None
    total_macs_per_cycle = replica_count * int(candidate["block_macs_per_cycle"])
    total_vector_ops_per_cycle = max(1, int(math.ceil(total_macs_per_cycle * vector_ops_per_mac)))
    row = _shape_row(
        label="llama7b_proxy",
        layers=32,
        hidden_size=4096,
        attention_heads=32,
        sequence_length=sequence_length,
        kv_sharing="gqa8",
        kv_bits=8,
        die_area_mm2=die_area_mm2,
        sram_area_fraction=sram_area_fraction,
        usable_sram_fraction=usable_sram_fraction,
        bitcell_area_um2_per_bit=0.02,
        local_sram_fraction=local_sram_fraction,
        stack_count=8,
        pseudo_channels_per_stack=16,
        pseudo_channel_width_bits=64,
        data_rate_mtps=9000,
        hbm_efficiency=0.75,
        tile_tokens=tile_tokens,
        prefetch_distance_tiles=4,
        hbm_outstanding=16,
        arbitration_efficiency=0.85,
        virtual_channels=4,
        prefetch_start="during_qkv",
        bank_count=bank_count,
        bank_bandwidth_bytes_per_cycle=2048.0,
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        noc_bandwidth_bytes_per_cycle=32768.0,
        noc_hops=1,
        router_latency_cycles_per_hop=2,
        macs_per_cycle=total_macs_per_cycle,
        vector_ops_per_cycle=total_vector_ops_per_cycle,
        clock_ns=float(candidate["block_clock_ns"]),
    )
    row.update(
        {
            "compute_arch": candidate["compute_arch"],
            "compute_replica_count": replica_count,
            "compute_logic_area_fraction": logic_area_fraction,
            "reserved_area_fraction": reserved_area_fraction,
            "compute_budget_um2": round(compute_budget_um2, 6),
            "compute_area_um2": round(replica_count * float(candidate["block_area_um2"]), 6),
            "compute_power_mw": round(replica_count * float(candidate["block_power_mw"]), 6),
            "measured_block_macs_per_cycle": candidate["block_macs_per_cycle"],
            "measured_block_clock_ns": candidate["block_clock_ns"],
            "measured_block_area_um2": candidate["block_area_um2"],
            "measured_block_power_mw": candidate["block_power_mw"],
            "metrics_csv": candidate["metrics_csv"],
            "metrics_tag": candidate["metrics_tag"],
            "metrics_param_hash": candidate["metrics_param_hash"],
            "vector_ops_per_mac_assumption": vector_ops_per_mac,
        }
    )
    return row


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
    vector_ops_per_mac: float,
) -> JsonDict:
    candidates = _load_compute_candidates(
        repo_root=repo_root,
        tag_substring=tag_substring,
        compute_source=compute_source,
    )
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
                                    for candidate in candidates:
                                        row = _shape_with_compute(
                                            candidate=candidate,
                                            die_area_mm2=die_area_mm2,
                                            sram_area_fraction=sram_area_fraction,
                                            logic_area_fraction=logic_area_fraction,
                                            reserved_area_fraction=reserved_area_fraction,
                                            vector_ops_per_mac=vector_ops_per_mac,
                                            sequence_length=sequence_length,
                                            usable_sram_fraction=usable_sram_fraction,
                                            local_sram_fraction=local_sram_fraction,
                                            tile_tokens=tile_tokens,
                                            bank_count=bank_count,
                                        )
                                        if row is None:
                                            skipped_area_budget += 1
                                        else:
                                            rows.append(row)
    if not rows:
        raise RuntimeError("no rows generated; area budget may be too small for measured compute blocks")
    rows_sorted = sorted(rows, key=lambda row: row["latency_us"])
    dominance: dict[str, int] = {}
    for row in rows:
        key = str(row["dominant_tile_resource"])
        dominance[key] = dominance.get(key, 0) + 1
    return {
        "version": 0.1,
        "model": "llm_decoder_attention_kv_measured_compute_llama7b_v1",
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
        "best_by_die_sram_logic": _best_by(
            rows,
            (
                "sequence_length",
                "die_area_mm2",
                "sram_area_fraction",
                "compute_logic_area_fraction",
            ),
        ),
        "best_by_compute_arch": _best_by(rows, ("sequence_length", "die_area_mm2", "compute_arch")),
        "assumptions": [
            "Compute throughput is derived from merged compute PPA: replica_count * measured block MACs/cycle.",
            "Block clock period is the measured critical path for the selected PPA row; HBM service remains derived from physical MT/s.",
            "Only quality-backed native-GQA KV8 is ranked here; KV4/MQA remain excluded from deployable candidates.",
            "Compute area is constrained by an explicit die-area fraction after SRAM and reserved non-SRAM/non-compute area.",
            "Vector throughput is not separately measured for the attention softmax path; it is tied to MAC throughput by vector_ops_per_mac.",
            "This remains a planning model, not a detailed NoC arbitration or SRAM macro floorplan.",
        ],
    }


def _write_markdown(path: Path, payload: JsonDict) -> None:
    best = payload["best"]
    lines = [
        "# Decoder Attention/KV Measured Compute Substitution",
        "",
        f"- model: `{payload['model']}`",
        f"- generated_row_count: `{payload['sweep_summary']['generated_row_count']}`",
        f"- skipped_area_budget_count: `{payload['sweep_summary']['skipped_area_budget_count']}`",
        "",
        "## Best",
        "",
        "| seq | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | clock ns | compute area um2 | compute mW | latency us | resource |",
        "|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|",
        "| {seq} | {die} | {sram} | {logic} | {arch} | {rep} | {macs} | {clk} | {area} | {pwr} | {lat} | {res} |".format(
            seq=best["sequence_length"],
            die=best["die_area_mm2"],
            sram=best["sram_area_fraction"],
            logic=best["compute_logic_area_fraction"],
            arch=best["compute_arch"],
            rep=best["compute_replica_count"],
            macs=best["macs_per_cycle"],
            clk=best["clock_ns"],
            area=best["compute_area_um2"],
            pwr=best["compute_power_mw"],
            lat=best["latency_us"],
            res=best["dominant_tile_resource"],
        ),
        "",
        "## Best By Die",
        "",
        "| seq | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | hbm share | latency us | resource |",
        "|---:|---:|---:|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["best_by_die"]:
        lines.append(
            "| {seq} | {die} | {sram} | {logic} | {arch} | {rep} | {macs} | {share} | {lat} | {res} |".format(
                seq=row["sequence_length"],
                die=row["die_area_mm2"],
                sram=row["sram_area_fraction"],
                logic=row["compute_logic_area_fraction"],
                arch=row["compute_arch"],
                rep=row["compute_replica_count"],
                macs=row["macs_per_cycle"],
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
            "| rank | die | SRAM frac | logic frac | arch | replicas | MAC/cyc | vec/cyc | clock ns | latency us | resource |",
            "|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for index, row in enumerate(payload["top_rows"][:10], start=1):
        lines.append(
            "| {rank} | {die} | {sram} | {logic} | {arch} | {rep} | {macs} | {vec} | {clk} | {lat} | {res} |".format(
                rank=index,
                die=row["die_area_mm2"],
                sram=row["sram_area_fraction"],
                logic=row["compute_logic_area_fraction"],
                arch=row["compute_arch"],
                rep=row["compute_replica_count"],
                macs=row["macs_per_cycle"],
                vec=row["vector_ops_per_cycle"],
                clk=row["clock_ns"],
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
    ap.add_argument("--tile-tokens-list", type=_int_list, default=[512, 1024])
    ap.add_argument("--bank-count", type=_int_list, default=[16, 64])
    ap.add_argument("--vector-ops-per-mac", type=float, default=0.125)
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

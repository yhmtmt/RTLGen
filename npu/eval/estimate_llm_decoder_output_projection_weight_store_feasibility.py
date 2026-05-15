#!/usr/bin/env python3
"""Estimate resident output-projection weight-store banking feasibility."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _float_list(value: str) -> list[float]:
    parsed = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed or any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("expected comma-separated positive floats")
    return parsed


def _int_list(value: str) -> list[int]:
    parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not parsed or any(item <= 0 for item in parsed):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return parsed


def _ceil_div(a: float, b: float) -> int:
    if b <= 0:
        raise ValueError("divisor must be positive")
    return int(math.ceil(a / b))


def _shape_targets(memory_hierarchy: JsonDict) -> list[JsonDict]:
    targets: list[JsonDict] = []
    for summary in memory_hierarchy.get("shape_summaries", []):
        if not isinstance(summary, dict):
            continue
        best = summary.get("best_parallel")
        if not isinstance(best, dict):
            continue
        targets.append(
            {
                "label": summary.get("label"),
                "sequence_length": summary.get("sequence_length"),
                "hidden_size": summary.get("hidden_size"),
                "vocab_size": summary.get("vocab_size"),
                "baseline_producer_us": summary.get("baseline_producer_us"),
                "best_parallel_us": best.get("producer_latency_us_parallel"),
                "producer_lanes": best.get("producer_lanes"),
                "macs_per_cycle": best.get("macs_per_cycle"),
                "target_local_cache_bw_bytes_per_cycle": best.get("local_cache_bw_bytes_per_cycle"),
                "target_cache_capacity_mb": best.get("cache_capacity_mb"),
                "target_cache_hit_rate": best.get("effective_cache_hit_rate"),
                "resident_weight_mb": best.get("resident_weight_mb"),
                "cache_weight_mb": best.get("cache_weight_mb"),
                "weight_bytes_per_tile": best.get("weight_bytes_per_tile"),
                "local_weight_cycles_per_tile": best.get("local_weight_cycles_per_tile"),
                "producer_ii_cycles_parallel": best.get("producer_ii_cycles_parallel"),
            }
        )
    return targets


def _candidate_row(
    *,
    target: JsonDict,
    bank_capacity_mb: float,
    bank_read_width_bits: int,
    read_ports_per_bank: int,
    area_budget_mm2: float,
    bitcell_area_um2_per_bit: float,
    peripheral_area_overhead: float,
) -> JsonDict:
    cache_weight_mb = float(target.get("cache_weight_mb") or target.get("resident_weight_mb") or 0.0)
    target_bw = float(target.get("target_local_cache_bw_bytes_per_cycle") or 0.0)
    weight_bytes_per_tile = float(target.get("weight_bytes_per_tile") or 0.0)
    target_cycles = int(target.get("local_weight_cycles_per_tile") or 0)
    read_width_bytes = bank_read_width_bits / 8.0
    bank_bw = read_width_bytes * read_ports_per_bank
    capacity_banks = _ceil_div(cache_weight_mb, bank_capacity_mb)
    bandwidth_banks = _ceil_div(target_bw, bank_bw)
    banks = max(capacity_banks, bandwidth_banks)
    aggregate_bw = banks * bank_bw
    aggregate_read_bits = int(banks * bank_read_width_bits * read_ports_per_bank)
    delivered_cycles = _ceil_div(weight_bytes_per_tile, aggregate_bw)
    provisioned_capacity_mb = banks * bank_capacity_mb
    storage_bits = provisioned_capacity_mb * 1024.0 * 1024.0 * 8.0
    proxy_area_mm2 = storage_bits * bitcell_area_um2_per_bit * (1.0 + peripheral_area_overhead) / 1_000_000.0
    capacity_ok = provisioned_capacity_mb >= cache_weight_mb
    bandwidth_ok = aggregate_bw >= target_bw and (target_cycles <= 0 or delivered_cycles <= target_cycles)
    area_ok = proxy_area_mm2 <= area_budget_mm2
    return {
        "label": target.get("label"),
        "sequence_length": target.get("sequence_length"),
        "hidden_size": target.get("hidden_size"),
        "vocab_size": target.get("vocab_size"),
        "producer_lanes": target.get("producer_lanes"),
        "target_local_cache_bw_bytes_per_cycle": target_bw,
        "target_cache_hit_rate": target.get("target_cache_hit_rate"),
        "cache_weight_mb": cache_weight_mb,
        "resident_weight_mb": target.get("resident_weight_mb"),
        "weight_bytes_per_tile": weight_bytes_per_tile,
        "target_local_weight_cycles_per_tile": target_cycles,
        "bank_capacity_mb": bank_capacity_mb,
        "bank_read_width_bits": bank_read_width_bits,
        "read_ports_per_bank": read_ports_per_bank,
        "bank_bw_bytes_per_cycle": bank_bw,
        "capacity_banks": capacity_banks,
        "bandwidth_banks": bandwidth_banks,
        "required_banks": banks,
        "provisioned_capacity_mb": round(provisioned_capacity_mb, 6),
        "aggregate_bw_bytes_per_cycle": round(aggregate_bw, 6),
        "aggregate_read_bits_per_cycle": aggregate_read_bits,
        "delivered_local_weight_cycles_per_tile": delivered_cycles,
        "area_budget_mm2": area_budget_mm2,
        "bitcell_area_um2_per_bit": bitcell_area_um2_per_bit,
        "peripheral_area_overhead": peripheral_area_overhead,
        "proxy_storage_area_mm2": round(proxy_area_mm2, 6),
        "capacity_ok": capacity_ok,
        "bandwidth_ok": bandwidth_ok,
        "area_budget_ok": area_ok,
        "feasible_under_budget": capacity_ok and bandwidth_ok and area_ok,
        "dominant_requirement": "bandwidth" if bandwidth_banks >= capacity_banks else "capacity",
    }


def _best(rows: list[JsonDict], *, require_area: bool) -> JsonDict | None:
    candidates = [
        row
        for row in rows
        if row.get("capacity_ok") and row.get("bandwidth_ok") and (row.get("area_budget_ok") or not require_area)
    ]
    return min(
        candidates,
        key=lambda row: (
            int(row["required_banks"]),
            float(row["proxy_storage_area_mm2"]),
            int(row["aggregate_read_bits_per_cycle"]),
        ),
        default=None,
    )


def build_report(
    *,
    memory_hierarchy: JsonDict,
    bank_capacity_mb_list: list[float],
    bank_read_width_bits_list: list[int],
    read_ports_per_bank_list: list[int],
    area_budget_mm2_list: list[float],
    bitcell_area_um2_per_bit: float,
    peripheral_area_overhead: float,
) -> JsonDict:
    targets = _shape_targets(memory_hierarchy)
    rows: list[JsonDict] = []
    for target in targets:
        for bank_capacity in bank_capacity_mb_list:
            for read_width in bank_read_width_bits_list:
                for ports in read_ports_per_bank_list:
                    for area_budget in area_budget_mm2_list:
                        rows.append(
                            _candidate_row(
                                target=target,
                                bank_capacity_mb=bank_capacity,
                                bank_read_width_bits=read_width,
                                read_ports_per_bank=ports,
                                area_budget_mm2=area_budget,
                                bitcell_area_um2_per_bit=bitcell_area_um2_per_bit,
                                peripheral_area_overhead=peripheral_area_overhead,
                            )
                        )

    shape_summaries: list[JsonDict] = []
    for target in targets:
        shape_rows = [row for row in rows if row.get("label") == target.get("label")]
        shape_summaries.append(
            {
                **target,
                "best_capacity_bandwidth": _best(shape_rows, require_area=False),
                "best_area_budget_feasible": _best(shape_rows, require_area=True),
                "area_budget_feasible_count": sum(1 for row in shape_rows if row.get("feasible_under_budget")),
                "capacity_bandwidth_feasible_count": sum(
                    1 for row in shape_rows if row.get("capacity_ok") and row.get("bandwidth_ok")
                ),
            }
        )

    global_best_area = _best(rows, require_area=True)
    decision = (
        "weight_store_area_budget_feasible"
        if global_best_area
        else "weight_store_capacity_bandwidth_feasible_area_unbounded"
        if _best(rows, require_area=False)
        else "weight_store_infeasible_in_sweep"
    )
    return {
        "version": 0.1,
        "model": "decoder_output_projection_weight_store_feasibility_v1",
        "inputs": {
            "memory_hierarchy_model": memory_hierarchy.get("model"),
            "bank_capacity_mb_list": bank_capacity_mb_list,
            "bank_read_width_bits_list": bank_read_width_bits_list,
            "read_ports_per_bank_list": read_ports_per_bank_list,
            "area_budget_mm2_list": area_budget_mm2_list,
            "bitcell_area_um2_per_bit": bitcell_area_um2_per_bit,
            "peripheral_area_overhead": peripheral_area_overhead,
        },
        "summary": {
            "shape_count": len(targets),
            "row_count": len(rows),
            "area_budget_feasible_rows": sum(1 for row in rows if row.get("feasible_under_budget")),
            "capacity_bandwidth_feasible_rows": sum(
                1 for row in rows if row.get("capacity_ok") and row.get("bandwidth_ok")
            ),
            "global_best_capacity_bandwidth": _best(rows, require_area=False),
            "global_best_area_budget_feasible": global_best_area,
        },
        "shape_summaries": shape_summaries,
        "weight_store_sweep": rows,
        "decision": {
            "decision": decision,
            "next_step": (
                "If area-budget feasible rows exist, queue a bounded RTL wrapper for the selected sharded "
                "weight-store interface; otherwise revisit external memory or model partitioning before RTL."
            ),
        },
        "assumptions": [
            "This is a banking and storage proxy, not a generated SRAM macro or routed memory subsystem.",
            "The proxy area is bitcell_area_um2_per_bit times stored bits plus peripheral overhead.",
            "Aggregate read bandwidth assumes banks can be read independently and combined by a distributed producer fabric.",
            "The aggregate_read_bits_per_cycle field is an interface-width pressure indicator, not necessarily one physical bus.",
            "Targets come from the best parallel producer memory-hierarchy rows after ranker calibration.",
        ],
    }


def write_markdown(path: str | Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output-Projection Weight-Store Feasibility",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- row_count: `{payload['summary']['row_count']}`",
        f"- area_budget_feasible_rows: `{payload['summary']['area_budget_feasible_rows']}`",
        "",
        "## Shape Summary",
        "",
        "| shape | cache_mb | target_bw_Bpc | best banks | read bits/cyc | proxy_area_mm2 | budget_ok | dominant |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["shape_summaries"]:
        best = row.get("best_area_budget_feasible") or row.get("best_capacity_bandwidth") or {}
        lines.append(
            "| {label} | {cache} | {bw} | {banks} | {bits} | {area} | `{ok}` | {dom} |".format(
                label=row.get("label"),
                cache=row.get("cache_weight_mb"),
                bw=row.get("target_local_cache_bw_bytes_per_cycle"),
                banks=best.get("required_banks"),
                bits=best.get("aggregate_read_bits_per_cycle"),
                area=best.get("proxy_storage_area_mm2"),
                ok=best.get("area_budget_ok"),
                dom=best.get("dominant_requirement"),
            )
        )
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--memory-hierarchy", required=True)
    ap.add_argument("--bank-capacity-mb-list", type=_float_list, default=[0.5, 1.0, 2.0, 4.0, 8.0])
    ap.add_argument("--bank-read-width-bits-list", type=_int_list, default=[256, 512, 1024, 2048])
    ap.add_argument("--read-ports-per-bank-list", type=_int_list, default=[1, 2])
    ap.add_argument("--area-budget-mm2-list", type=_float_list, default=[25.0, 100.0, 400.0])
    ap.add_argument("--bitcell-area-um2-per-bit", type=float, default=0.2)
    ap.add_argument("--peripheral-area-overhead", type=float, default=0.35)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()
    payload = build_report(
        memory_hierarchy=_load_json(args.memory_hierarchy),
        bank_capacity_mb_list=args.bank_capacity_mb_list,
        bank_read_width_bits_list=args.bank_read_width_bits_list,
        read_ports_per_bank_list=args.read_ports_per_bank_list,
        area_budget_mm2_list=args.area_budget_mm2_list,
        bitcell_area_um2_per_bit=args.bitcell_area_um2_per_bit,
        peripheral_area_overhead=args.peripheral_area_overhead,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "out": str(out), "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

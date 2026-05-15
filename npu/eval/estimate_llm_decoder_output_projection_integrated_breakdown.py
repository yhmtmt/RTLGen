#!/usr/bin/env python3
"""Account for producer plus output-ranker wrapper PPA and service behavior."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load_json(path: str | Path) -> JsonDict:
    with Path(path).open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(float(value))


def _read_aggregate_rows(path: str | Path) -> list[JsonDict]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = [dict(row) for row in csv.DictReader(f)]
    return [row for row in rows if row.get("scope") == "aggregate"]


def _parse_lane_map(raw: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        key, sep, value = part.partition("=")
        if not sep:
            raise ValueError(f"lane map entry must be arch=lanes: {part}")
        out[key.strip()] = int(value)
    return out


def _ranker_by_lane(wrapper_physical: JsonDict) -> dict[int, JsonDict]:
    variants = wrapper_physical.get("variants")
    if not isinstance(variants, list):
        raise ValueError("wrapper physical JSON missing variants list")
    out: dict[int, JsonDict] = {}
    for variant in variants:
        if isinstance(variant, dict):
            out[_int(variant.get("producer_lanes"))] = variant
    return out


def _policy_summary(policy: JsonDict) -> dict[int, JsonDict]:
    rows = policy.get("policy_rows")
    if not isinstance(rows, list):
        return {}
    summary: dict[int, JsonDict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        producer = row.get("producer")
        if not isinstance(producer, dict):
            continue
        lanes = _int(producer.get("producer_lanes"))
        entry = summary.setdefault(
            lanes,
            {
                "producer_lanes": lanes,
                "rows": 0,
                "serial_lpc1_rows": 0,
                "ranktree_rows": 0,
                "producer_ii_cycles_min": None,
                "producer_ii_cycles_max": None,
            },
        )
        entry["rows"] += 1
        selected = str(row.get("selected_path", ""))
        if selected == "serial_lpc1":
            entry["serial_lpc1_rows"] += 1
        elif "ranktree" in selected:
            entry["ranktree_rows"] += 1
        ii = _int(producer.get("producer_ii_cycles"))
        entry["producer_ii_cycles_min"] = ii if entry["producer_ii_cycles_min"] is None else min(entry["producer_ii_cycles_min"], ii)
        entry["producer_ii_cycles_max"] = ii if entry["producer_ii_cycles_max"] is None else max(entry["producer_ii_cycles_max"], ii)
    return summary


def _simulation_cycles(variant: JsonDict, name: str) -> int:
    simulations = variant.get("simulations")
    if not isinstance(simulations, dict):
        return 0
    sim = simulations.get(name)
    if not isinstance(sim, dict):
        return 0
    observed = sim.get("observed")
    if not isinstance(observed, dict):
        return 0
    return _int(observed.get("final_cycle"))


def build_report(
    *,
    producer_rows: list[JsonDict],
    wrapper_physical: JsonDict,
    policy: JsonDict,
    lane_map: dict[str, int],
    source_refs: JsonDict,
) -> JsonDict:
    rankers = _ranker_by_lane(wrapper_physical)
    policy_by_lane = _policy_summary(policy)
    integrations: list[JsonDict] = []
    checks: list[JsonDict] = [
        {
            "name": "ranker_wrapper_physical_measured",
            "passed": (wrapper_physical.get("decision") or {}).get("decision")
            == "output_projection_ranker_wrapper_physical_measured",
            "observed": (wrapper_physical.get("decision") or {}).get("decision"),
        },
        {
            "name": "ranker_policy_promoted",
            "passed": (policy.get("decision") or {}).get("decision")
            == "output_projection_ranker_policy_promoted",
            "observed": (policy.get("decision") or {}).get("decision"),
        },
    ]

    for producer in producer_rows:
        arch_id = str(producer.get("arch_id", ""))
        lanes = lane_map.get(arch_id)
        ranker = rankers.get(lanes or -1)
        if ranker is None:
            integrations.append(
                {
                    "arch_id": arch_id,
                    "macro_mode": producer.get("macro_mode"),
                    "producer_lanes": lanes,
                    "status": "missing_ranker_lane_mapping",
                }
            )
            continue
        ranker_metrics = ranker.get("metrics_row") if isinstance(ranker.get("metrics_row"), dict) else {}
        producer_cp = _float(producer.get("critical_path_ns_mean"))
        ranker_cp = _float(ranker_metrics.get("critical_path_ns"))
        producer_area = _float(producer.get("die_area_um2_mean"))
        ranker_area = _float(ranker_metrics.get("die_area"))
        producer_power = _float(producer.get("total_power_mw_mean"))
        ranker_power = _float(ranker_metrics.get("total_power_mw"))
        integrated_cp = max(producer_cp, ranker_cp)
        serial_cycles = _simulation_cycles(ranker, "serial")
        ranktree_cycles = _simulation_cycles(ranker, "ranktree")
        row = {
            "arch_id": arch_id,
            "macro_mode": producer.get("macro_mode"),
            "producer_lanes": lanes,
            "status": "ok",
            "producer": {
                "critical_path_ns": producer_cp,
                "area_um2": producer_area,
                "power_mw": producer_power,
                "latency_ms_mean": _float(producer.get("latency_ms_mean")),
                "energy_mj_mean": _float(producer.get("energy_mj_mean")),
                "flow_elapsed_s_mean": _float(producer.get("flow_elapsed_s_mean")),
            },
            "ranker_wrapper": {
                "critical_path_ns": ranker_cp,
                "area_um2": ranker_area,
                "power_mw": ranker_power,
                "serial_final_cycle": serial_cycles,
                "ranktree_final_cycle": ranktree_cycles,
                "serial_service_ns_at_ranker_cp": serial_cycles * ranker_cp,
                "ranktree_service_ns_at_ranker_cp": ranktree_cycles * ranker_cp,
                "policy_summary": policy_by_lane.get(lanes or -1, {}),
            },
            "integrated_accounting": {
                "critical_path_ns_max": integrated_cp,
                "timing_bottleneck": "ranker_wrapper" if ranker_cp > producer_cp else "producer",
                "area_um2_sum": producer_area + ranker_area,
                "ranker_area_over_producer": ranker_area / producer_area if producer_area else None,
                "power_mw_sum": producer_power + ranker_power,
                "ranker_power_over_producer": ranker_power / producer_power if producer_power else None,
            },
        }
        integrations.append(row)

    ok_rows = [row for row in integrations if row.get("status") == "ok"]
    area_overheads = [
        float(row["integrated_accounting"]["ranker_area_over_producer"])
        for row in ok_rows
        if row.get("integrated_accounting", {}).get("ranker_area_over_producer") is not None
    ]
    power_overheads = [
        float(row["integrated_accounting"]["ranker_power_over_producer"])
        for row in ok_rows
        if row.get("integrated_accounting", {}).get("ranker_power_over_producer") is not None
    ]
    checks.append(
        {
            "name": "all_producer_arches_have_ranker_mapping",
            "passed": len(ok_rows) == len(integrations) and bool(integrations),
            "observed": {"ok": len(ok_rows), "total": len(integrations)},
        }
    )
    checks.append(
        {
            "name": "ranker_not_timing_bottleneck",
            "passed": all(row.get("integrated_accounting", {}).get("timing_bottleneck") == "producer" for row in ok_rows),
            "observed": [
                {
                    "arch_id": row.get("arch_id"),
                    "macro_mode": row.get("macro_mode"),
                    "timing_bottleneck": row.get("integrated_accounting", {}).get("timing_bottleneck"),
                }
                for row in ok_rows
            ],
        }
    )

    max_area_overhead = max(area_overheads) if area_overheads else None
    max_power_overhead = max(power_overheads) if power_overheads else None
    low_overhead = (
        max_area_overhead is not None
        and max_power_overhead is not None
        and max_area_overhead <= 0.15
        and max_power_overhead <= 0.20
    )
    checks.append(
        {
            "name": "ranker_overhead_within_first_order_budget",
            "passed": low_overhead,
            "observed": {
                "max_ranker_area_over_producer": max_area_overhead,
                "max_ranker_power_over_producer": max_power_overhead,
                "budget": {"area": 0.15, "power": 0.20},
            },
        }
    )

    decision = (
        "producer_output_ranker_integration_accounting_passed"
        if all(check["passed"] for check in checks)
        else "producer_output_ranker_integration_needs_refinement"
    )
    return {
        "version": 0.1,
        "model": "decoder_output_projection_producer_ranker_integration_v1",
        "source_refs": source_refs,
        "assumptions": [
            "This is an additive accounting model over independently measured producer and ranker-wrapper macros; it is not a routed monolithic integration.",
            "The default lane map treats fp16_nm1 as a 64-lane output tile producer and fp16_nm2 as a 128-lane output tile producer.",
            "Wrapper power includes inactive serial or rank-tree path because no clock gating was modeled in the physical wrapper measurement.",
        ],
        "checks": checks,
        "integrations": integrations,
        "summary": {
            "ok_integrations": len(ok_rows),
            "total_integrations": len(integrations),
            "max_ranker_area_over_producer": max_area_overhead,
            "max_ranker_power_over_producer": max_power_overhead,
        },
        "decision": {
            "decision": decision,
            "next_step": (
                "Use the additive breakdown as the producer-side integration baseline, then decide whether to add clock/path gating or a monolithic routed wrapper."
                if decision.endswith("_passed")
                else "Refine lane mapping, split serial/rank-tree wrappers, or add gating before treating the wrapper as producer-integrated."
            ),
        },
    }


def write_markdown(path: str | Path, payload: JsonDict) -> None:
    lines = [
        "# Decoder Output Projection Producer/Ranker Integration",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- next_step: {payload['decision']['next_step']}",
        "",
        "## Integration Rows",
        "",
        "| arch | macro | lanes | bottleneck | cp ns | ranker area/prod | ranker power/prod | serial cycles | ranktree cycles |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in payload["integrations"]:
        acct = row.get("integrated_accounting") or {}
        ranker = row.get("ranker_wrapper") or {}
        lines.append(
            "| {arch} | {macro} | {lanes} | {bottleneck} | {cp:.4f} | {area:.4f} | {power:.4f} | {serial} | {ranktree} |".format(
                arch=row.get("arch_id"),
                macro=row.get("macro_mode"),
                lanes=row.get("producer_lanes"),
                bottleneck=acct.get("timing_bottleneck"),
                cp=_float(acct.get("critical_path_ns_max")),
                area=_float(acct.get("ranker_area_over_producer")),
                power=_float(acct.get("ranker_power_over_producer")),
                serial=ranker.get("serial_final_cycle"),
                ranktree=ranker.get("ranktree_final_cycle"),
            )
        )
    lines.extend(["", "## Checks", "", "| check | passed | observed |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--producer-summary", required=True)
    ap.add_argument("--ranker-wrapper-physical", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--lane-map", default="fp16_nm1=64,fp16_nm2=128")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    source_refs = {
        "producer_summary": args.producer_summary,
        "ranker_wrapper_physical": args.ranker_wrapper_physical,
        "policy": args.policy,
        "lane_map": args.lane_map,
    }
    payload = build_report(
        producer_rows=_read_aggregate_rows(args.producer_summary),
        wrapper_physical=_load_json(args.ranker_wrapper_physical),
        policy=_load_json(args.policy),
        lane_map=_parse_lane_map(args.lane_map),
        source_refs=source_refs,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

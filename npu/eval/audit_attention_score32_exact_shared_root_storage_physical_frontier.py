#!/usr/bin/env python3
"""Audit measured PPA for the exact shared-root registered-SRAM bank frontier."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]
_BANKS = (2, 4, 8, 15)
_MACRO_NAME = "fakeram45_64x32"
_MACRO_AREA_UM2 = 20.140 * 61.600
_DEFAULT_BANK_REPORT = Path(
    "npu/docs/generated/attention_score32_exact_stats_once_banked_root_frontier.json"
)
_DEFAULT_DESIGN_ROOT = Path("runs/designs/npu_blocks")


def _positive(value: object, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if parsed <= 0.0:
        raise ValueError(f"{label} must be positive")
    return parsed


def _integer(value: object, label: str) -> int:
    parsed = _positive(value, label)
    if not parsed.is_integer():
        raise ValueError(f"{label} must be an integer")
    return int(parsed)


def _json_cell(value: object, label: str) -> Any:
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must contain JSON") from exc


def _bank_contract(bank_report: JsonDict) -> dict[int, JsonDict]:
    if bank_report.get("semantic_profile") != "score32_exact_stats_once_banked_root_macro_v2":
        raise ValueError("bank frontier semantic profile mismatch")
    points = {
        int(point["physical_banks"]): dict(point)
        for point in list(bank_report.get("rtl_macro_points") or [])
    }
    if set(points) != set(_BANKS):
        raise ValueError(f"bank frontier must contain exactly {_BANKS}")
    for banks, point in points.items():
        if point.get("bit_exact") is not True:
            raise ValueError(f"B{banks} is not bit exact")
        _integer(point.get("fakeram45_64x32_macros"), f"B{banks} expected macro count")
        _integer(point.get("full_chain_final_cycle"), f"B{banks} full-chain cycle")
    return points


def _metrics_path(design_root: Path, banks: int) -> Path:
    return (
        design_root
        / f"attention_score32_exact_shared_root_storage_macro_b{banks}"
        / "metrics.csv"
    )


def _load_bank_rows(*, path: Path, contract: JsonDict, banks: int) -> list[JsonDict]:
    if not path.is_file():
        raise ValueError(f"B{banks} metrics are missing: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    ok_rows = [row for row in source_rows if str(row.get("status") or "").strip() == "ok"]
    if not ok_rows:
        raise ValueError(f"B{banks} has no status=ok physical row")

    expected_macros = _integer(
        contract.get("fakeram45_64x32_macros"), f"B{banks} expected macro count"
    )
    final_cycles = _integer(contract.get("full_chain_final_cycle"), f"B{banks} final cycles")
    nominal_macro_area = expected_macros * _MACRO_AREA_UM2
    rows: list[JsonDict] = []
    for index, source in enumerate(ok_rows, start=1):
        label = f"B{banks} row {index}"
        macro_count = _integer(source.get("macro_count"), f"{label} macro_count")
        if macro_count != expected_macros:
            raise ValueError(
                f"{label} macro_count mismatch: expected {expected_macros}, got {macro_count}"
            )
        blackboxes = _json_cell(source.get("blackbox_instance_counts"), f"{label} blackboxes")
        if not isinstance(blackboxes, dict) or int(blackboxes.get(_MACRO_NAME, -1)) != expected_macros:
            raise ValueError(f"{label} does not prove {expected_macros} {_MACRO_NAME} instances")
        missing = _json_cell(source.get("missing_blackboxes"), f"{label} missing_blackboxes")
        if missing != []:
            raise ValueError(f"{label} has missing blackboxes: {missing}")
        if not str(source.get("macro_manifest_path") or "").strip():
            raise ValueError(f"{label} macro_manifest_path is missing")

        critical_path_ns = _positive(source.get("critical_path_ns"), f"{label} critical path")
        total_power_mw = _positive(source.get("total_power_mw"), f"{label} total power")
        stdcell_area_um2 = _positive(source.get("stdcell_area_um2"), f"{label} stdcell area")
        macro_area_um2 = _positive(source.get("macro_area_um2"), f"{label} macro area")
        instance_area_um2 = _positive(source.get("instance_area_um2"), f"{label} instance area")
        if abs(macro_area_um2 - nominal_macro_area) > 0.02 * nominal_macro_area:
            raise ValueError(
                f"{label} macro area {macro_area_um2} does not match nominal {nominal_macro_area}"
            )
        if abs(instance_area_um2 - (stdcell_area_um2 + macro_area_um2)) > max(
            1.0, 1.0e-4 * instance_area_um2
        ):
            raise ValueError(f"{label} instance area is inconsistent with stdcell plus macro area")

        params = _json_cell(source.get("params_json"), f"{label} params_json")
        if not isinstance(params, dict):
            raise ValueError(f"{label} params_json must be an object")
        requested_period_ns = _positive(params.get("CLOCK_PERIOD"), f"{label} clock period")
        full_chain_latency_ns = final_cycles * critical_path_ns
        rows.append(
            {
                "candidate_id": f"shared_root_storage_b{banks}_{source.get('tag') or index}",
                "physical_banks": banks,
                "tag": source.get("tag"),
                "requested_period_ns": requested_period_ns,
                "critical_path_ns": critical_path_ns,
                "timing_slack_ns": requested_period_ns - critical_path_ns,
                "timing_met": critical_path_ns <= requested_period_ns + 1.0e-9,
                "full_chain_final_cycles": final_cycles,
                "full_chain_latency_ns": full_chain_latency_ns,
                "component_completions_per_s": 1.0e9 / full_chain_latency_ns,
                "stdcell_area_um2": stdcell_area_um2,
                "macro_area_um2": macro_area_um2,
                "instance_area_um2": instance_area_um2,
                "macro_count": macro_count,
                "total_power_mw": total_power_mw,
                "vectorless_full_chain_energy_nj": total_power_mw
                * full_chain_latency_ns
                / 1000.0,
                "bit_exact": True,
                "precision_effect": "none_packet_storage_is_bit_exact",
                "source_metrics": str(path),
            }
        )
    return rows


def _dominates(left: JsonDict, right: JsonDict) -> bool:
    left_values = (
        float(left["full_chain_latency_ns"]),
        float(left["instance_area_um2"]),
        float(left["vectorless_full_chain_energy_nj"]),
    )
    right_values = (
        float(right["full_chain_latency_ns"]),
        float(right["instance_area_um2"]),
        float(right["vectorless_full_chain_energy_nj"]),
    )
    return all(a <= b for a, b in zip(left_values, right_values)) and any(
        a < b for a, b in zip(left_values, right_values)
    )


def build_report(*, bank_report: JsonDict, design_root: Path) -> JsonDict:
    contracts = _bank_contract(bank_report)
    measured_rows = [
        row
        for banks in _BANKS
        for row in _load_bank_rows(
            path=_metrics_path(design_root, banks),
            contract=contracts[banks],
            banks=banks,
        )
    ]
    eligible = [row for row in measured_rows if row["timing_met"]]
    if not eligible:
        raise ValueError("no measured row meets its requested clock period")
    pareto = [
        row for row in eligible if not any(_dominates(other, row) for other in eligible if other is not row)
    ]

    def winner(metric: str) -> list[str]:
        target = min(float(row[metric]) for row in eligible)
        return [str(row["candidate_id"]) for row in eligible if float(row[metric]) == target]

    return {
        "version": 1,
        "semantic_profile": "score32_exact_shared_root_storage_physical_frontier_v1",
        "source_bank_profile": bank_report["semantic_profile"],
        "measured_rows": measured_rows,
        "timing_eligible_candidate_ids": [row["candidate_id"] for row in eligible],
        "pareto_candidate_ids": [row["candidate_id"] for row in pareto],
        "dimension_winners": {
            "full_chain_latency": winner("full_chain_latency_ns"),
            "embodied_instance_area": winner("instance_area_um2"),
            "vectorless_full_chain_energy": winner("vectorless_full_chain_energy_nj"),
            "precision": [row["candidate_id"] for row in eligible],
        },
        "selection_status": "physical_bank_frontier_measured_no_scalar_weighting",
        "precision_contract": {
            "status": "unchanged",
            "reason": "all storage/replay candidates preserve the exact packet bits and final rows",
        },
        "remaining_abstractions": [
            "OpenROAD vectorless power is a screening metric, not workload-toggle-complete energy.",
            "The component completion energy is not yet multiplied by the Llama7B hierarchical invocation schedule.",
            "Vendor SRAM signoff is represented by the available fakeram45 Liberty/LEF model.",
        ],
        "next_action": (
            "Substitute each Pareto bank row into the exact finite-endpoint Llama7B schedule and rerank "
            "token throughput, total embodied area, and per-token energy without changing precision evidence."
        ),
    }


def render_markdown(report: JsonDict) -> str:
    lines = [
        "# Exact Shared-Root Storage Physical Frontier",
        "",
        "| candidate | banks | macros | requested ns | postroute ns | full-chain ns | area um2 | power mW | energy nJ | timing |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["measured_rows"]:
        lines.append(
            "| {candidate_id} | {physical_banks} | {macro_count} | {requested_period_ns:.4f} | "
            "{critical_path_ns:.4f} | {full_chain_latency_ns:.4f} | {instance_area_um2:.4f} | "
            "{total_power_mw:.6f} | {vectorless_full_chain_energy_nj:.6f} | {timing_met} |".format(
                **row
            )
        )
    lines.extend(["", "## Pareto Candidates", ""])
    lines.extend(f"- `{candidate}`" for candidate in report["pareto_candidate_ids"])
    lines.extend(["", "## Dimension Winners", ""])
    for dimension, candidates in report["dimension_winners"].items():
        lines.append(f"- {dimension}: {', '.join(f'`{value}`' for value in candidates)}")
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in report["remaining_abstractions"])
    lines.extend(["", "## Next Action", "", report["next_action"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--bank-report", type=Path, default=_DEFAULT_BANK_REPORT)
    parser.add_argument("--design-root", type=Path, default=_DEFAULT_DESIGN_ROOT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    bank_report = json.loads((root / args.bank_report).read_text(encoding="utf-8"))
    report = build_report(bank_report=bank_report, design_root=root / args.design_root)
    out_path = root / args.out
    report_path = root / args.report
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

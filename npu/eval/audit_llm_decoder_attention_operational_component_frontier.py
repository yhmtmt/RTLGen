#!/usr/bin/env python3
"""Replace proxy component area/timing in the Llama7B attention frontier."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def _load(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _positive(value: Any, label: str) -> float:
    result = _float(value)
    if result <= 0.0:
        raise ValueError(f"{label} must be positive")
    return result


def _metrics_rows(path: Path) -> list[JsonDict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    rows = [row for row in rows if str(row.get("status") or "").strip() == "ok"]
    if not rows:
        raise ValueError(f"no status=ok metrics rows: {path}")
    for row in rows:
        row["metrics_csv"] = str(path)
    return rows


def _select_row(rows: list[JsonDict], *, clock_ns: float) -> JsonDict:
    timing_feasible = [row for row in rows if _float(row.get("critical_path_ns"), 1.0e99) <= clock_ns]
    candidates = timing_feasible or rows
    return min(
        candidates,
        key=lambda row: (
            _float(row.get("instance_area_um2"), 1.0e99),
            _float(row.get("critical_path_ns"), 1.0e99),
            _float(row.get("total_power_mw"), 1.0e99),
        ),
    )


def _dense_component(row: JsonDict) -> JsonDict:
    for component in row.get("components", []):
        if isinstance(component, dict) and component.get("component") == "dense_int8_gemm_fabric":
            return component
    raise ValueError(f"frontier row {row.get('candidate_id')} has no dense_int8_gemm_fabric component")


def _matching_old_tile_row(component: JsonDict, rows: list[JsonDict]) -> JsonDict:
    component_area = _positive(component.get("area_um2"), "dense component area")
    component_power = _positive(component.get("power_mw"), "dense component power")

    def error(row: JsonDict) -> tuple[float, float]:
        area = _positive(row.get("instance_area_um2"), "old tile area")
        power = _positive(row.get("total_power_mw"), "old tile power")
        area_replicas = component_area / area
        power_replicas = component_power / power
        return abs(area_replicas - round(area_replicas)), abs(power_replicas - round(power_replicas))

    return min(rows, key=error)


def _replace_dense(
    row: JsonDict,
    *,
    old_tile: JsonDict,
    operational_tile: JsonDict,
) -> JsonDict:
    updated = deepcopy(row)
    dense = _dense_component(updated)
    old_area = _positive(old_tile.get("instance_area_um2"), "old tile instance area")
    old_power = _positive(old_tile.get("total_power_mw"), "old tile power")
    old_dense_area = _positive(dense.get("area_um2"), "old dense fabric area")
    old_dense_power = _positive(dense.get("power_mw"), "old dense fabric power")
    area_replicas = int(round(old_dense_area / old_area))
    active_replicas = int(round(old_dense_power / old_power))
    if area_replicas < 1 or active_replicas < 1:
        raise ValueError("invalid dense tile replica count")

    operational_area = _positive(operational_tile.get("instance_area_um2"), "operational tile area")
    operational_power = _positive(operational_tile.get("total_power_mw"), "operational tile power")
    operational_delay = _positive(operational_tile.get("critical_path_ns"), "operational tile delay")
    operational_dense_area = operational_area * area_replicas
    area_delta_mm2 = (operational_dense_area - old_dense_area) / 1.0e6

    dense.update(
        {
            "component": "operational_dense_int8_gemm_fabric",
            "area_um2": round(operational_dense_area, 6),
            "critical_path_ns": operational_delay,
            "clock_ok": operational_delay <= _positive(updated.get("source_schedule_clock_ns"), "schedule clock"),
            "source": operational_tile.get("metrics_csv"),
            "area_replica_count": area_replicas,
            "active_replica_count": active_replicas,
            "per_tile_area_um2": operational_area,
            "vectorless_power_mw_per_tile": operational_power,
            "vectorless_power_mw_scaled_active": round(operational_power * active_replicas, 12),
            "power_mw": old_dense_power,
            "energy_mj_per_token": dense.get("energy_mj_per_token"),
            "power_accounting": "retained_activity_backed_frontier_energy",
        }
    )
    updated["logic_plus_service_area_mm2"] = round(
        _positive(updated.get("logic_plus_service_area_mm2"), "logic plus service area") + area_delta_mm2,
        12,
    )
    updated["retained_logic_area_mm2"] = round(
        _positive(updated.get("retained_logic_area_mm2"), "retained logic area") + area_delta_mm2,
        12,
    )
    updated["embodied_logic_plus_score_macro_area_mm2"] = round(
        _positive(updated.get("embodied_logic_plus_score_macro_area_mm2"), "embodied area") + area_delta_mm2,
        12,
    )
    updated["operational_dense_area_delta_mm2"] = round(area_delta_mm2, 12)
    updated["operational_dense_tile_metrics"] = {
        "metrics_csv": operational_tile.get("metrics_csv"),
        "critical_path_ns": operational_delay,
        "instance_area_um2": operational_area,
        "vectorless_power_mw": operational_power,
        "area_replica_count": area_replicas,
        "active_replica_count": active_replicas,
    }
    updated["energy_recost_status"] = "retained_activity_backed_energy_vectorless_power_not_substituted"
    updated["timing_ok"] = bool(updated.get("timing_ok", True)) and dense["clock_ok"]
    return updated


def _replace_score_bank(row: JsonDict, *, score_bank: JsonDict | None) -> JsonDict:
    if score_bank is None:
        return row
    updated = deepcopy(row)
    bank_count = int(updated.get("head_count") or 0)
    if bank_count < 1:
        raise ValueError("head_count must be positive for score-bank recost")
    bank_area = _positive(score_bank.get("instance_area_um2"), "score bank instance area")
    bank_delay = _positive(score_bank.get("critical_path_ns"), "score bank critical path")
    bank_power = _positive(score_bank.get("total_power_mw"), "score bank vectorless power")
    old_score_area = _positive(updated.get("score_sram_macro_area_mm2"), "old score SRAM area")
    new_score_area = bank_area * bank_count / 1.0e6
    delta = new_score_area - old_score_area
    updated["score_sram_macro_area_mm2"] = round(new_score_area, 12)
    updated["embodied_logic_plus_score_macro_area_mm2"] = round(
        _positive(updated.get("embodied_logic_plus_score_macro_area_mm2"), "embodied area") + delta,
        12,
    )
    updated["score_bank_proxy_area_delta_mm2"] = round(delta, 12)
    updated["score_bank_proxy_metrics"] = {
        "metrics_csv": score_bank.get("metrics_csv"),
        "critical_path_ns": bank_delay,
        "instance_area_um2_per_bank": bank_area,
        "vectorless_power_mw_per_bank": bank_power,
        "bank_count": bank_count,
        "fakeram_macro_count_per_bank": 56,
        "sram_signoff": False,
    }
    updated["timing_ok"] = bool(updated.get("timing_ok", True)) and (
        bank_delay <= _positive(updated.get("source_schedule_clock_ns"), "schedule clock")
    )
    return updated


def build_report(
    *,
    frontier_json: Path,
    operational_tile_metrics_csv: Path,
    old_tile_metrics_csv: Path,
    score_bank_metrics_csv: Path | None = None,
) -> JsonDict:
    frontier = _load(frontier_json)
    rows = [row for row in frontier.get("rows", []) if isinstance(row, dict)]
    if not rows:
        raise ValueError("frontier has no rows")
    schedule_clock = max(_positive(row.get("source_schedule_clock_ns"), "source schedule clock") for row in rows)
    operational_tile = _select_row(_metrics_rows(operational_tile_metrics_csv), clock_ns=schedule_clock)
    old_rows = _metrics_rows(old_tile_metrics_csv)
    old_tile = _matching_old_tile_row(_dense_component(rows[0]), old_rows)
    score_bank = (
        _select_row(_metrics_rows(score_bank_metrics_csv), clock_ns=schedule_clock)
        if score_bank_metrics_csv is not None
        else None
    )

    updated_rows: list[JsonDict] = []
    for source in rows:
        updated = _replace_dense(source, old_tile=old_tile, operational_tile=operational_tile)
        updated = _replace_score_bank(updated, score_bank=score_bank)
        abstractions = [str(item) for item in updated.get("remaining_abstractions", [])]
        abstractions = [item for item in abstractions if "dense" not in item.lower() or "schedule" in item.lower()]
        abstractions.extend(
            [
                "operational dense-tile power is vectorless; activity-backed token energy is retained pending SAIF/VCD calibration",
                "tile replicas, score banks, divider service, and local routing remain physically uncomposed",
            ]
        )
        if score_bank is None:
            abstractions.append("score-bank proxy PNR is pending")
        else:
            abstractions.append("score-bank FakeRAM LEF/LIB views have no SRAM GDS and are not signoff")
        updated["remaining_abstractions"] = list(dict.fromkeys(abstractions))
        updated["candidate_id"] = f"{source.get('candidate_id')}_operational_components"
        updated["family"] = "score32_separated_two_pass_operational_components"
        updated_rows.append(updated)

    area_rank = sorted(
        updated_rows,
        key=lambda row: (
            _float(row.get("embodied_logic_plus_score_macro_area_mm2"), 1.0e99),
            _float(row.get("latency_us"), 1.0e99),
        ),
    )
    latency_rank = sorted(
        updated_rows,
        key=lambda row: (
            _float(row.get("latency_us"), 1.0e99),
            _float(row.get("embodied_logic_plus_score_macro_area_mm2"), 1.0e99),
        ),
    )
    return {
        "version": 1,
        "decision": "operational_component_area_timing_recosted_energy_retained",
        "inputs": {
            "frontier_json": str(frontier_json),
            "operational_tile_metrics_csv": str(operational_tile_metrics_csv),
            "old_tile_metrics_csv": str(old_tile_metrics_csv),
            "score_bank_metrics_csv": str(score_bank_metrics_csv) if score_bank_metrics_csv else None,
        },
        "measurement_policy": {
            "area": "replace narrow dense harness and optional analytical score SRAM with measured operational instance area",
            "timing": "require measured components to fit the inherited schedule clock",
            "energy": "retain activity-backed frontier energy; never substitute vectorless OpenROAD power",
            "precision": "inherit the already-passed mixed-int8 Llama7B quality gate unchanged",
        },
        "selected_operational_tile": operational_tile,
        "selected_old_tile": old_tile,
        "selected_score_bank": score_bank,
        "rows": updated_rows,
        "latency_rank": latency_rank,
        "area_rank": area_rank,
        "diagnosis": {
            "recommended_candidate": latency_rank[0]["candidate_id"],
            "recommended_latency_us": latency_rank[0]["latency_us"],
            "recommended_token_throughput_per_s": latency_rank[0]["token_throughput_per_s"],
            "recommended_energy_mj_per_token": latency_rank[0]["energy_mj_per_token"],
            "recommended_embodied_area_mm2": latency_rank[0]["embodied_logic_plus_score_macro_area_mm2"],
            "energy_promotion_blocked": True,
            "next_step": "measure activity-backed operational tile power and physically compose one local cluster",
        },
    }


def _write_report(payload: JsonDict, path: Path) -> None:
    diagnosis = payload["diagnosis"]
    lines = [
        "# Llama7B operational component frontier",
        "",
        f"- decision: `{payload['decision']}`",
        f"- recommended candidate: `{diagnosis['recommended_candidate']}`",
        f"- latency: `{diagnosis['recommended_latency_us']}` us",
        f"- throughput: `{diagnosis['recommended_token_throughput_per_s']}` token/s",
        f"- retained activity-backed energy: `{diagnosis['recommended_energy_mj_per_token']}` mJ/token",
        f"- embodied area: `{diagnosis['recommended_embodied_area_mm2']}` mm2",
        "- vectorless-power energy promotion: `blocked`",
        "",
        "| candidate | latency us | token/s | energy mJ/token | embodied mm2 | timing ok |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in payload["latency_rank"]:
        lines.append(
            f"| {row['candidate_id']} | {row['latency_us']} | {row['token_throughput_per_s']} | "
            f"{row['energy_mj_per_token']} | {row['embodied_logic_plus_score_macro_area_mm2']} | "
            f"{row['timing_ok']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier-json", type=Path, required=True)
    parser.add_argument("--operational-tile-metrics-csv", type=Path, required=True)
    parser.add_argument("--old-tile-metrics-csv", type=Path, required=True)
    parser.add_argument("--score-bank-metrics-csv", type=Path)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(
        frontier_json=args.frontier_json,
        operational_tile_metrics_csv=args.operational_tile_metrics_csv,
        old_tile_metrics_csv=args.old_tile_metrics_csv,
        score_bank_metrics_csv=args.score_bank_metrics_csv,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(payload, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

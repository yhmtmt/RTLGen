#!/usr/bin/env python3
"""Calibrate producer/ranker coupling with measured policy-wrapper service."""

from __future__ import annotations

import argparse
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


def _as_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(float(value))


def _as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def _wrapper_by_lanes(wrapper_physical: JsonDict) -> dict[int, JsonDict]:
    out: dict[int, JsonDict] = {}
    for row in wrapper_physical.get("variants", []):
        if isinstance(row, dict):
            out[_as_int(row.get("producer_lanes"))] = row
    return out


def _policy_index(policy: JsonDict) -> dict[tuple[int, int, int, int, float, int], JsonDict]:
    index: dict[tuple[int, int, int, int, float, int], JsonDict] = {}
    for row in policy.get("policy_rows", []):
        if not isinstance(row, dict):
            continue
        producer = row.get("producer")
        if not isinstance(producer, dict):
            continue
        key = (
            _as_int(producer.get("vocab_size")),
            _as_int(producer.get("hidden_size")),
            _as_int(producer.get("producer_lanes")),
            _as_int(producer.get("macs_per_cycle")),
            _as_float(producer.get("memory_bandwidth_bytes_per_cycle")),
            _as_int(producer.get("producer_ii_cycles")),
        )
        index[key] = row
    return index


def _scenario_from_policy(row: JsonDict | None, *, producer_ii_cycles: int) -> tuple[str, str]:
    if row is not None:
        selected = str(row.get("selected_path") or "")
        if selected == "serial_lpc1":
            return "serial", selected
        if "ranktree" in selected:
            return "ranktree", selected
    return ("serial", "threshold_serial_lpc1") if producer_ii_cycles >= 384 else ("ranktree", "threshold_ranktree")


def _simulation_cycles(wrapper: JsonDict, scenario: str) -> int:
    simulations = wrapper.get("simulations") if isinstance(wrapper.get("simulations"), dict) else {}
    sim = simulations.get(scenario) if isinstance(simulations.get(scenario), dict) else {}
    observed = sim.get("observed") if isinstance(sim.get("observed"), dict) else {}
    return _as_int(observed.get("final_cycle"))


def _wrapper_clock_ns(wrapper: JsonDict) -> float:
    metrics = wrapper.get("metrics_row") if isinstance(wrapper.get("metrics_row"), dict) else {}
    return _as_float(metrics.get("critical_path_ns"))


def _best(rows: list[JsonDict], key: str) -> JsonDict | None:
    ok = [row for row in rows if row.get("status") == "ok"]
    if not ok:
        return None
    return min(
        ok,
        key=lambda row: (
            _as_float(row.get(key), float("inf")),
            _as_float(row.get("calibrated_candidate_memory_bytes"), float("inf")),
            _as_int(row.get("producer_lanes"), 10**9),
        ),
    )


def build_report(
    *,
    coupled_report: JsonDict,
    wrapper_physical: JsonDict,
    policy: JsonDict,
) -> JsonDict:
    wrappers = _wrapper_by_lanes(wrapper_physical)
    policies = _policy_index(policy)
    calibrated_rows: list[JsonDict] = []

    for row in coupled_report.get("coupled_ranker_sweep", []):
        if not isinstance(row, dict):
            continue
        lanes = _as_int(row.get("producer_lanes"))
        wrapper = wrappers.get(lanes)
        if wrapper is None:
            calibrated_rows.append({**row, "status": "missing_wrapper_physical"})
            continue
        key = (
            _as_int(row.get("vocab_size")),
            _as_int(row.get("hidden_size")),
            lanes,
            _as_int(row.get("macs_per_cycle")),
            _as_float(row.get("memory_bandwidth_bytes_per_cycle")),
            _as_int(row.get("producer_ii_cycles")),
        )
        policy_row = policies.get(key)
        scenario, selected_path = _scenario_from_policy(
            policy_row,
            producer_ii_cycles=_as_int(row.get("producer_ii_cycles")),
        )
        cycles = _simulation_cycles(wrapper, scenario)
        clock_ns = _wrapper_clock_ns(wrapper)
        if cycles <= 0 or clock_ns <= 0.0:
            calibrated_rows.append(
                {
                    **row,
                    "status": "missing_wrapper_service_measurement",
                    "policy_match": policy_row is not None,
                    "calibrated_selected_path": selected_path,
                    "calibrated_scenario": scenario,
                    "calibrated_ranker_cycles": cycles,
                    "calibrated_ranker_clock_ns": clock_ns,
                }
            )
            continue
        measured_ranker_us = cycles * clock_ns / 1000.0
        producer_us = _as_float(row.get("producer_latency_us_per_token"))
        calibrated_us = max(producer_us, measured_ranker_us)
        calibrated_rows.append(
            {
                **row,
                "status": "ok",
                "policy_match": policy_row is not None,
                "calibrated_selected_path": selected_path,
                "calibrated_scenario": scenario,
                "calibrated_ranker_cycles": cycles,
                "calibrated_ranker_clock_ns": clock_ns,
                "calibrated_ranker_latency_us_per_token": round(measured_ranker_us, 6),
                "calibrated_coupled_latency_us_per_token": round(calibrated_us, 6),
                "old_ranker_latency_us_per_token": row.get("ranker_latency_us_per_token"),
                "old_coupled_latency_us_per_token": row.get("coupled_latency_us_per_token"),
                "calibrated_dominant_term": "ranker_policy_wrapper" if measured_ranker_us > producer_us else "producer",
                "calibrated_candidate_memory_bytes": row.get("ranker_candidate_memory_bytes"),
            }
        )

    old_best = _best(calibrated_rows, "coupled_latency_us_per_token")
    calibrated_best = _best(calibrated_rows, "calibrated_coupled_latency_us_per_token")
    speedup = None
    if old_best and calibrated_best:
        old_us = _as_float(old_best.get("coupled_latency_us_per_token"))
        new_us = _as_float(calibrated_best.get("calibrated_coupled_latency_us_per_token"))
        speedup = round(old_us / new_us, 6) if new_us > 0 else None

    producer_dominant = [
        row for row in calibrated_rows if row.get("status") == "ok" and row.get("calibrated_dominant_term") == "producer"
    ]
    ok_count = sum(1 for row in calibrated_rows if row.get("status") == "ok")
    missing_wrapper_count = sum(1 for row in calibrated_rows if row.get("status") == "missing_wrapper_physical")
    bad_measurement_count = sum(
        1 for row in calibrated_rows if row.get("status") == "missing_wrapper_service_measurement"
    )
    return {
        "version": 0.1,
        "model": "decoder_output_projection_producer_ranker_policy_calibration_v1",
        "inputs": {
            "coupled_model": coupled_report.get("model"),
            "wrapper_model": wrapper_physical.get("model"),
            "policy_model": policy.get("model"),
        },
        "checks": [
            {
                "name": "wrapper_physical_measured",
                "passed": (wrapper_physical.get("decision") or {}).get("decision")
                == "output_projection_ranker_wrapper_physical_measured",
                "observed": (wrapper_physical.get("decision") or {}).get("decision"),
            },
            {
                "name": "policy_promoted",
                "passed": (policy.get("decision") or {}).get("decision")
                == "output_projection_ranker_policy_promoted",
                "observed": (policy.get("decision") or {}).get("decision"),
            },
            {
                "name": "measured_wrapper_lane_rows_calibrated",
                "passed": ok_count > 0 and bad_measurement_count == 0,
                "observed": {
                    "ok": ok_count,
                    "missing_wrapper_physical": missing_wrapper_count,
                    "missing_wrapper_service_measurement": bad_measurement_count,
                    "total": len(calibrated_rows),
                },
            },
        ],
        "old_best": old_best,
        "calibrated_best": calibrated_best,
        "summary": {
            "row_count": len(calibrated_rows),
            "calibrated_row_count": ok_count,
            "missing_wrapper_physical_rows": missing_wrapper_count,
            "missing_wrapper_service_measurement_rows": bad_measurement_count,
            "producer_dominant_rows": len(producer_dominant),
            "ranker_dominant_rows": sum(
                1 for row in calibrated_rows if row.get("status") == "ok" and row.get("calibrated_dominant_term") != "producer"
            ),
            "old_to_calibrated_best_latency_speedup": speedup,
        },
        "calibrated_coupled_ranker_sweep": calibrated_rows,
        "decision": {
            "decision": "producer_ranker_policy_calibration_completed",
            "next_step": (
                "Refresh frontier synthesis with calibrated producer/ranker latency; if output projection still dominates, "
                "measure producer weight-memory/cache hierarchy rather than the ranker wrapper."
            ),
        },
        "assumptions": [
            "The measured policy wrapper service is used only for ranker service after a producer tile reaches the ranker.",
            "Producer latency and II remain from the existing output-projection service model.",
            "Exact policy rows are used when available; otherwise the serial_lpc1 threshold is applied conservatively.",
            "This calibration replaces the older streaming ranker hierarchy latency for output-projection policy-wrapper coupling.",
        ],
    }


def write_markdown(path: str | Path, payload: JsonDict) -> None:
    old_best = payload.get("old_best") or {}
    new_best = payload.get("calibrated_best") or {}
    lines = [
        "# Decoder Producer/Ranker Policy Calibration",
        "",
        f"- model: `{payload['model']}`",
        f"- decision: `{payload['decision']['decision']}`",
        f"- old_best_us: `{old_best.get('coupled_latency_us_per_token')}`",
        f"- calibrated_best_us: `{new_best.get('calibrated_coupled_latency_us_per_token')}`",
        f"- old_to_calibrated_speedup: `{payload['summary'].get('old_to_calibrated_best_latency_speedup')}`",
        f"- producer_dominant_rows: `{payload['summary'].get('producer_dominant_rows')}`",
        f"- ranker_dominant_rows: `{payload['summary'].get('ranker_dominant_rows')}`",
        "",
        "## Best Row",
        "",
        "| metric | old | calibrated |",
        "|---|---:|---:|",
        f"| coupled_us | {old_best.get('coupled_latency_us_per_token')} | {new_best.get('calibrated_coupled_latency_us_per_token')} |",
        f"| producer_us | {old_best.get('producer_latency_us_per_token')} | {new_best.get('producer_latency_us_per_token')} |",
        f"| ranker_us | {old_best.get('ranker_latency_us_per_token')} | {new_best.get('calibrated_ranker_latency_us_per_token')} |",
        f"| lanes | {old_best.get('producer_lanes')} | {new_best.get('producer_lanes')} |",
        f"| selected_path |  | {new_best.get('calibrated_selected_path')} |",
        "",
        "## Checks",
        "",
        "| check | passed | observed |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| {check['name']} | `{check['passed']}` | `{check.get('observed')}` |")
    lines.extend(["", "## Assumptions", ""])
    for item in payload["assumptions"]:
        lines.append(f"- {item}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coupled-report", required=True)
    ap.add_argument("--wrapper-physical", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    payload = build_report(
        coupled_report=_load_json(args.coupled_report),
        wrapper_physical=_load_json(args.wrapper_physical),
        policy=_load_json(args.policy),
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "out": args.out, "out_md": args.out_md}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

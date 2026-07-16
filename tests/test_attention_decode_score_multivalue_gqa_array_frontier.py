from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from npu.eval.audit_attention_decode_score_multivalue_gqa_array_frontier import (
    _pareto,
    _parse_metrics_row,
    _recost_candidate,
    build_report,
)


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _prior(tmp_path: Path) -> Path:
    source = _write(
        tmp_path / "source.json",
        {
            "source_schedule": {
                "hidden_size": 4096,
                "attention_heads": 32,
                "kv_heads": 4,
                "sequence_length": 131072,
                "clock_ns": 6.0,
                "layers": 32,
                "compute_budget_um2": 400_000_000,
                "logic_area_used_um2": 399_000_000,
                "compute_area_um2": 396_000_000,
                "measured_shared_sram_used_area_um2": 240_000_000,
                "measured_tile_local_sram_area_um2": 40_000_000,
                "command_dispatch_cycles": 2,
                "kv_write_cycles": 10,
            }
        },
    )
    middle = _write(tmp_path / "middle.json", {"inputs": {"prior_frontier_json": source.name}})
    return _write(
        tmp_path / "prior.json",
        {
            "model": "decoder_attention_decode_score_multivalue_gqa_group_frontier_llama7b_v1",
            "decision": "measured_complete_gqa8_group_component_frontier_promoted",
            "precision": {"status": "exact"},
            "inputs": {"prior_frontier_json": middle.name},
            "schedule_contract": {"group_full_context_cycles": 300},
            "dense_qkv_tile": {"area_um2": 10_000, "effective_macs_per_cycle": 8.0},
            "rows": [
                {
                    "group_count": count,
                    "group_area_mm2": 2.0 * count,
                    "latency_us": 1000.0 / count,
                    "token_throughput_per_s": 100.0 * count,
                    "clock_ns": 8.0,
                    "gqa_group_component_energy_mj_per_token": 1.792,
                }
                for count in (1, 2, 4)
            ],
            "best_throughput_candidate": {"candidate_id": "prior", "token_throughput_per_s": 400.0},
        },
    )


def _equivalence(tmp_path: Path) -> Path:
    return _write(
        tmp_path / "equivalence.json",
        {
            "model": "llama7b_gqa8_multigroup_array_compositional_equivalence_v1",
            "decision": "llama7b_gqa8_multigroup_array_equivalence_pass",
            "equivalence_pass": True,
            "precision_status": "exact",
            "measured_group_counts": [1, 2, 4],
        },
    )


def _metrics(path: Path, rows: list[dict[str, object]]) -> Path:
    fields = [
        "design", "platform", "config_hash", "param_hash", "tag", "status",
        "critical_path_ns", "die_area", "params_json", "result_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _metric_row(count: int, *, area: float = 1_000_000, cp: float = 7.0, clock: float = 8.0) -> dict[str, object]:
    return {
        "design": f"array_g{count}", "platform": "nangate45", "config_hash": f"config{count}",
        "param_hash": f"param{count}", "tag": "tag", "status": "ok", "critical_path_ns": cp,
        "die_area": area, "params_json": json.dumps({"CLOCK_PERIOD": clock, "FLOW_VARIANT": "array_v1", "GROUP_COUNT": count, "CORE_UTILIZATION": 50}),
        "result_path": "result.json",
    }


def test_formulas_use_direct_area_and_expected_gqa_work(tmp_path: Path) -> None:
    prior = _prior(tmp_path)
    report = build_report(
        prior_frontier_json=prior,
        array_equivalence_json=_equivalence(tmp_path),
        array_metrics={count: _metrics(tmp_path / f"g{count}.csv", [_metric_row(count, area=1_000_000 * count)]) for count in (1, 2, 4)},
    )
    rows = {row["group_count"]: row for row in report["rows"]}
    assert rows[1]["direct_array_instance_area_um2"] == 1_000_000
    assert rows[2]["direct_array_instance_area_um2"] == 2_000_000
    assert rows[1]["qkv_work"] == 4096**2 + 2 * 4096 * 4 * 128
    assert rows[1]["group_waves_per_layer"] == 4
    assert rows[4]["attention_cycles"] == 300
    assert rows[1]["clock_ns"] == 8.0
    assert rows[1]["energy_status"].startswith("NOT_")
    assert report["promotion"]["direct_array_timing"] == "promoted"


def test_parser_preserves_failed_and_negative_rows(tmp_path: Path) -> None:
    failed = _parse_metrics_row(
        {"status": "failed", "params_json": json.dumps({"CLOCK_PERIOD": 8})},
        metrics_path=tmp_path / "m.csv", count=1, line=2,
    )
    assert failed["accepted"] is False
    assert "status is failed" in failed["reason"]
    negative = _parse_metrics_row(
        {"status": "ok", "critical_path_ns": 7, "die_area": -1, "params_json": json.dumps({"CLOCK_PERIOD": 8})},
        metrics_path=tmp_path / "m.csv", count=1, line=3,
    )
    assert negative["accepted"] is False
    assert "instance area" in negative["reason"]


def test_contract_rejection(tmp_path: Path) -> None:
    prior = _prior(tmp_path)
    equivalence = _equivalence(tmp_path)
    payload = json.loads(equivalence.read_text(encoding="utf-8"))
    payload["measured_group_counts"] = [1, 2]
    equivalence.write_text(json.dumps(payload), encoding="utf-8")
    paths = {count: _metrics(tmp_path / f"g{count}.csv", [_metric_row(count)]) for count in (1, 2, 4)}
    with pytest.raises(ValueError, match="contract"):
        build_report(prior_frontier_json=prior, array_equivalence_json=equivalence, array_metrics=paths)


def test_pareto_uses_latency_area_and_compositional_energy() -> None:
    def row(name: str, latency: float, area: float, energy: float, fit: bool = True) -> dict[str, object]:
        return {
            "candidate_id": name, "latency_us": latency,
            "embodied_logic_plus_shared_sram_area_mm2": area,
            "prior_compositional_gqa_group_component_energy_mj_per_token": energy,
            "compute_budget_area_fit": fit, "timing_feasible": True,
        }
    result = _pareto([row("fast", 1, 3, 2), row("small", 2, 1, 2), row("energy", 2, 2, 1), row("bad", 0.5, 0.5, 0.5, False)])
    assert {item["candidate_id"] for item in result} == {"fast", "small", "energy"}


def test_recost_direct_area_substitution() -> None:
    schedule = {
        "hidden_size": 4096, "attention_heads": 32, "kv_heads": 4, "layers": 32,
        "group_full_context_cycles": 300, "clock_ns": 6, "compute_budget_um2": 100_000,
        "logic_area_used_um2": 90_000, "compute_area_um2": 80_000,
        "measured_shared_sram_used_area_um2": 10, "measured_tile_local_sram_area_um2": 20,
    }
    row = _recost_candidate(
        group_count=1, schedule=schedule,
        dense_tile={"area_um2": 10_000, "effective_macs_per_cycle": 8},
        prior_row={"group_area_mm2": 0.001, "latency_us": 100, "token_throughput_per_s": 10, "clock_ns": 8, "gqa_group_component_energy_mj_per_token": 1},
        metric={"instance_area_um2": 40_000, "critical_path_ns": 7, "configured_clock_period_ns": 8, "param_hash": "p", "metrics_path": "m", "csv_line": 2, "config_hash": "c", "flow_variant": "v", "platform": "n", "die_area": 40_000, "core_area": None, "core_utilization": None, "params": {}},
    )
    assert row["direct_array_instance_area_um2"] == 40_000
    assert row["direct_array_instance_area_um2"] != 0.001 * 1e6

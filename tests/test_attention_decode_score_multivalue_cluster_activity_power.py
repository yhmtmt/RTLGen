#!/usr/bin/env python3
"""Tests for the multivalue-cluster activity power frontier audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest import mock

from npu.eval import audit_attention_decode_score_multivalue_cluster_activity_power as audit


def _write_metrics(path: Path) -> None:
    fields = [
        "design",
        "platform",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "instance_area_um2",
        "params_json",
    ]
    rows = [
        {
            "design": "cluster",
            "platform": "nangate45",
            "param_hash": "p10",
            "tag": "die2500",
            "status": "ok",
            "critical_path_ns": "7.0",
            "die_area": "6250000",
            "instance_area_um2": "3000000",
            "params_json": json.dumps(
                {"CLOCK_PERIOD": 10, "FLOW_VARIANT": "cluster_die2500"}
            ),
        },
        {
            "design": "cluster",
            "platform": "nangate45",
            "param_hash": "p8a",
            "tag": "die2500",
            "status": "ok",
            "critical_path_ns": "7.5",
            "die_area": "6250000",
            "instance_area_um2": "3100000",
            "params_json": json.dumps(
                {"CLOCK_PERIOD": 8, "FLOW_VARIANT": "cluster_die2500"}
            ),
        },
        {
            "design": "cluster",
            "platform": "nangate45",
            "param_hash": "p8b",
            "tag": "die3000",
            "status": "ok",
            "critical_path_ns": "8.1",
            "die_area": "9000000",
            "instance_area_um2": "3050000",
            "params_json": json.dumps(
                {"CLOCK_PERIOD": 8, "FLOW_VARIANT": "cluster_die3000"}
            ),
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_feasible_metrics_selects_exact_clock_and_timing(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    rows = audit._feasible_metrics(metrics, 8.0)
    assert [audit._params(row)["FLOW_VARIANT"] for row in rows] == ["cluster_die2500"]


def test_build_report_rejects_unproven_equivalence(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text('{"equivalence_pass": false}', encoding="utf-8")
    with mock.patch.object(audit, "generate_phase_activity") as generate:
        try:
            audit.build_report(
                config=tmp_path / "config.json",
                cluster_metrics_csv=tmp_path / "metrics.csv",
                equivalence_json=equivalence,
                orfs_design_config=tmp_path / "config.mk",
                clock_period_ns=8.0,
                activity_dir=tmp_path / "activity",
            )
        except ValueError as exc:
            assert "equivalence did not pass" in str(exc)
        else:
            raise AssertionError("unproven equivalence was accepted")
    generate.assert_not_called()


def test_build_report_records_promoted_and_failed_variants(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    # Make the second 8 ns row feasible so both physical variants are attempted.
    rows = list(csv.DictReader(metrics.open(encoding="utf-8")))
    rows[-1]["critical_path_ns"] = "7.9"
    with metrics.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "clock_period_ns": 8.0,
        "block_count": 3,
        "representative_full_transaction_cycles": 8334,
        "phase_partition_cycle_sum": 8334,
        "phases": [],
    }
    power_ok = {
        "promotion_gate_pass": True,
        "full_context_energy_j": 0.002,
        "full_context_cycles": 3399201,
        "full_context_latency_s": 0.027193608,
    }
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(
        json.dumps(
            {
                "equivalence_pass": True,
                "decision": "shared_score_multivalue_cluster_equivalent",
                "score_tensor_hash": "score-hash",
                "final_tensor_hash": "final-hash",
            }
        ),
        encoding="utf-8",
    )
    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit,
        "build_power_report",
        side_effect=[power_ok, RuntimeError("/orfs/missing result")],
    ):
        payload = audit.build_report(
            config=config,
            cluster_metrics_csv=metrics,
            equivalence_json=equivalence,
            orfs_design_config=tmp_path / "config.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
        )
    assert payload["decision"] == "activity_backed_cluster_power_measured"
    assert payload["source_dependencies"] == [
        "l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2",
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1",
    ]
    assert payload["promoted_candidate_count"] == 1
    assert payload["best_candidate_id"] == "multivalue_cluster_activity_cluster_die2500"
    assert payload["equivalence"]["final_tensor_hash"] == "final-hash"
    assert payload["candidates"][1]["status"] == "measurement_failed"
    assert "/orfs/" not in json.dumps(payload)

from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest import mock

import pytest

from npu.eval import audit_attention_decode_score_multivalue_gqa_group_activity_power as audit


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
            "design": "gqa_group",
            "platform": "nangate45",
            "param_hash": "group-a",
            "tag": "die7200",
            "status": "ok",
            "critical_path_ns": "7.0",
            "die_area": "51840000",
            "instance_area_um2": "3100000",
            "params_json": json.dumps({"CLOCK_PERIOD": 8, "FLOW_VARIANT": "group_die7200"}),
        },
        {
            "design": "gqa_group",
            "platform": "nangate45",
            "param_hash": "group-b",
            "tag": "die8000",
            "status": "ok",
            "critical_path_ns": "7.8",
            "die_area": "64000000",
            "instance_area_um2": "3200000",
            "params_json": json.dumps({"CLOCK_PERIOD": 8, "FLOW_VARIANT": "group_die8000"}),
        },
        {
            "design": "gqa_group",
            "platform": "nangate45",
            "param_hash": "slow",
            "tag": "die7200",
            "status": "ok",
            "critical_path_ns": "8.1",
            "die_area": "51840000",
            "instance_area_um2": "3000000",
            "params_json": json.dumps({"CLOCK_PERIOD": 8, "FLOW_VARIANT": "group_slow"}),
        },
        {
            "design": "gqa_group",
            "platform": "nangate45",
            "param_hash": "wrong-clock",
            "tag": "die7200",
            "status": "ok",
            "critical_path_ns": "7.0",
            "die_area": "51840000",
            "instance_area_um2": "2900000",
            "params_json": json.dumps({"CLOCK_PERIOD": 10, "FLOW_VARIANT": "group_wrong_clock"}),
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_baseline(path: Path, *, promoted: bool = True) -> None:
    path.write_text(
        json.dumps(
            {
                "model": "decoder_attention_decode_score_multivalue_cluster_activity_power_v1",
                "promotion_gate_pass": promoted,
                "best_candidate_id": "cluster_independent_variant",
                "best": {
                    "candidate_id": "cluster_independent_variant",
                    "flow_variant": "cluster_flow_that_must_not_be_paired",
                    "activity_power": {
                        "model": "postroute_phase_vcd_power_v1",
                        "promotion_gate_pass": promoted,
                        "clock_period_ns": 8.0,
                        "full_context_cycles": 7795,
                        "full_context_energy_j": 0.002,
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _power(energy: float) -> dict:
    return {
        "model": "postroute_phase_vcd_power_v1",
        "promotion_gate_pass": True,
        "clock_period_ns": 8.0,
        "full_context_cycles": 58207,
        "full_context_latency_s": 0.000465656,
        "full_context_energy_j": energy,
    }


def test_feasible_metrics_selects_timing_feasible_group_rows(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    rows = audit._feasible_metrics(metrics, 8.0)
    assert [audit._params(row)["FLOW_VARIANT"] for row in rows] == [
        "group_die7200",
        "group_die8000",
    ]


def test_build_report_gates_gqa_and_does_not_pair_cluster_flow(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(
        json.dumps(
            {
                "equivalence_pass": True,
                "decision": "llama7b_gqa8_shared_kv_equivalence_pass",
                "query_heads_per_kv": 8,
            }
        ),
        encoding="utf-8",
    )
    baseline = tmp_path / "cluster-power.json"
    _write_baseline(baseline)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    manifest = {
        "scope": "tb/dut",
        "scope_semantics": "the complete generated GQA8 group wrapper",
        "clock_period_ns": 8.0,
        "query_heads_per_kv": 8,
        "block_count": 3,
        "representative_full_transaction_cycles": 58307,
        "phase_partition_cycle_sum": 58307,
        "phases": [],
    }
    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit,
        "build_power_report",
        side_effect=[_power(0.014), RuntimeError("/orfs/private/result")],
    ) as build_power:
        payload = audit.build_report(
            config=config,
            group_metrics_csv=metrics,
            cluster_activity_power_json=baseline,
            equivalence_json=equivalence,
            group_orfs_design_config=tmp_path / "group.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
        )

    assert payload["decision"] == "activity_backed_gqa_group_power_measured"
    assert payload["best_candidate_id"] == "multivalue_gqa_group_activity_group_die7200"
    assert payload["independent_cluster_upper_bound_factor"] == 8
    best = payload["best"]
    assert best["direct_group_full_context_energy_j"] == 0.014
    assert best["independent_cluster_upper_bound"]["energy_j"] == pytest.approx(0.016)
    assert best["independent_cluster_upper_bound"]["pass"] is True
    assert payload["candidates"][1]["status"] == "measurement_failed"
    assert "/orfs/" not in json.dumps(payload["candidates"][1])
    assert [call.kwargs["flow_variant"] for call in build_power.call_args_list] == [
        "group_die7200",
        "group_die8000",
    ]


def test_build_report_rejects_unproven_gqa_equivalence(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text('{"equivalence_pass": false}', encoding="utf-8")
    with mock.patch.object(audit, "generate_phase_activity") as generate:
        with pytest.raises(ValueError, match="GQA8 shared-KV equivalence did not pass"):
            audit.build_report(
                config=tmp_path / "config.json",
                group_metrics_csv=tmp_path / "metrics.csv",
                cluster_activity_power_json=tmp_path / "cluster.json",
                equivalence_json=equivalence,
                group_orfs_design_config=tmp_path / "group.mk",
                clock_period_ns=8.0,
                activity_dir=tmp_path / "activity",
            )
    generate.assert_not_called()


def test_cluster_baseline_requires_measured_best_activity_power(tmp_path: Path) -> None:
    baseline = tmp_path / "cluster-power.json"
    _write_baseline(baseline, promoted=False)
    with pytest.raises(ValueError, match="not a promoted measured baseline"):
        audit._cluster_baseline(baseline, 8.0)

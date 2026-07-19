from __future__ import annotations

import csv
import json
from pathlib import Path
from unittest import mock

import pytest

from npu.eval import audit_attention_decode_score_multivalue_gqa_group_activity_power as audit


def _config(path: Path, parallel_query_head_lanes: int | None = None) -> None:
    path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_gqa_group_activity_power",
                "attention_decode_score_multivalue_gqa_group": {
                    "max_blocks": 16384,
                    "array_n": 8,
                    "value_slices": 16,
                    "divider_impl": "iterative_restoring",
                    "score_scale_lanes_per_cycle": 1,
                    "query_heads_per_kv": 8,
                    **({"parallel_query_head_lanes": parallel_query_head_lanes} if parallel_query_head_lanes else {}),
                },
            }
        ),
        encoding="utf-8",
    )


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
                "activity_contract": {
                    "clock_period_ns": 8.0,
                    "phases": [
                        {
                            "phase": "score_fill",
                            "full_context_cycles": 10,
                            "scaling": {"target_max_blocks": 16384},
                        },
                        {
                            "phase": "replay_value",
                            "full_context_cycles": 20,
                            "scaling": {"target_max_blocks": 16384},
                        },
                        {
                            "phase": "finalize_result",
                            "full_context_cycles": 7765,
                            "scaling": {"target_max_blocks": 16384},
                        },
                    ],
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
                "distinct_query_heads_pass": True,
                "shared_inputs_pass": True,
                "arithmetic_equivalence_pass": True,
                "wrapper_protocol": {"sharing_and_order_pass": True},
                "expected_group_result_sha256": "same-hash",
                "observed_group_result_sha256": "same-hash",
            }
        ),
        encoding="utf-8",
    )
    baseline = tmp_path / "cluster-power.json"
    _write_baseline(baseline)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    config = tmp_path / "config.json"
    _config(config, parallel_query_head_lanes=8)
    manifest = {
        "scope": "tb/dut",
        "scope_semantics": "the complete generated GQA8 group wrapper",
        "clock_period_ns": 8.0,
        "query_heads_per_kv": 8,
        "target_max_blocks": 16384,
        "block_count": 3,
        "representative_full_transaction_cycles": 58307,
        "phase_partition_cycle_sum": 58307,
        "phases": [
            {"phase": "score_fill"},
            {"phase": "replay_value"},
            {"phase": "finalize_result"},
        ],
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
    assert payload["independent_cluster_reference_factor"] == 8
    best = payload["best"]
    assert best["direct_group_full_context_energy_j"] == 0.014
    assert best["eight_independent_clusters_reference"]["energy_j"] == pytest.approx(0.016)
    assert best["eight_independent_clusters_reference"]["pass"] is True
    assert best["eight_independent_clusters_reference"]["is_formal_upper_bound"] is False
    assert payload["candidates"][1]["status"] == "measurement_failed"
    assert "/orfs/" not in json.dumps(payload["candidates"][1])
    assert [call.kwargs["flow_variant"] for call in build_power.call_args_list] == [
        "group_die7200",
        "group_die8000",
    ]


@pytest.mark.parametrize("parallel_query_head_lanes", [1, 2, 4, 8])
def test_build_report_accepts_folded_lane_equivalence_rows_for_configured_lanes(
    tmp_path: Path, parallel_query_head_lanes: int
) -> None:
    equivalence = tmp_path / "equivalence.json"
    shared_hash = "e2f07a3c580991601458466bfbaab4127cbcb654065b0241197f462ca4977069"
    rows = []
    completion_cycles = {1: 66671, 2: 62199, 4: 59963, 8: 58845}
    for lanes in [1, 2, 4, 8]:
        rows.append(
            {
                "equivalence_pass": True,
                "parallel_query_head_lanes": lanes,
                "query_head_waves": 8 // lanes,
                "completion_cycles": completion_cycles[lanes],
                "expected_group_result_sha256": shared_hash,
                "observed_group_result_sha256": shared_hash,
            }
        )
    equivalence.write_text(
        json.dumps(
            {
                "version": 1,
                "decision": "llama7b_gqa8_folded_lane_equivalence_pass",
                "query_heads_per_kv": 8,
                "rows": rows,
                "shared_result_sha256": shared_hash,
            }
        ),
        encoding="utf-8",
    )
    baseline = tmp_path / "cluster-power.json"
    _write_baseline(baseline)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics)
    config = tmp_path / "config.json"
    _config(config, parallel_query_head_lanes=parallel_query_head_lanes)
    manifest = {
        "query_head_waves": 8 // parallel_query_head_lanes,
        "query_heads_per_kv": 8,
        "parallel_query_head_lanes": parallel_query_head_lanes,
        "scope": "tb/dut",
        "scope_semantics": "the complete generated GQA8 group wrapper",
        "clock_period_ns": 8.0,
        "target_max_blocks": 16384,
        "block_count": 3,
        "representative_full_transaction_cycles": completion_cycles[parallel_query_head_lanes] + 1,
        "phase_partition_cycle_sum": completion_cycles[parallel_query_head_lanes] + 1,
        "phases": [
            {"phase": "score_fill"},
            {"phase": "replay_value"},
            {"phase": "finalize_result"},
        ],
    }
    with mock.patch.object(audit, "generate_phase_activity", return_value=manifest), mock.patch.object(
        audit,
        "build_power_report",
        return_value=_power(0.014),
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

        assert build_power.call_count == 2
        if parallel_query_head_lanes == 8:
            assert (
                payload["source_dependencies"]
                == [
                    "l2_decoder_attention_decode_score_multivalue_gqa8_group_equivalence_llama7b_v1",
                    "l1_decoder_attention_decode_score_multivalue_gqa8_group_pnr_v1",
                    "l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1",
                    "prior_single_cluster_activity_power_best_activity_power",
                ]
            )
        else:
            assert (
                payload["source_dependencies"]
                == [
                    "l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1",
                    f"l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes{parallel_query_head_lanes}_pnr_v1",
                    "l2_decoder_attention_decode_score_multivalue_cluster_activity_power_llama7b_v1",
                    "prior_single_cluster_activity_power_best_activity_power",
                ]
            )
        assert payload["equivalence"]["equivalence_pass"] is True
        assert payload["equivalence"]["parallel_query_head_lanes"] == parallel_query_head_lanes
        assert payload["equivalence"]["query_head_waves"] == 8 // parallel_query_head_lanes
        assert payload["equivalence"]["expected_group_result_sha256"] == shared_hash


def test_build_report_rejects_folded_lane_equivalence_hash_mismatch(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text(
        json.dumps(
            {
                "decision": "llama7b_gqa8_folded_lane_equivalence_pass",
                "query_heads_per_kv": 8,
                "shared_result_sha256": "shared-hash",
                "rows": [
                    {
                        "equivalence_pass": True,
                        "parallel_query_head_lanes": 1,
                        "expected_group_result_sha256": "row-hash",
                        "observed_group_result_sha256": "other-hash",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    _config(config, parallel_query_head_lanes=1)
    with pytest.raises(ValueError, match="did not pass for configured lane count"):
        audit.build_report(
            config=config,
            group_metrics_csv=tmp_path / "metrics.csv",
            cluster_activity_power_json=tmp_path / "cluster.json",
            equivalence_json=equivalence,
            group_orfs_design_config=tmp_path / "group.mk",
            clock_period_ns=8.0,
            activity_dir=tmp_path / "activity",
        )


def test_build_report_rejects_unproven_gqa_equivalence(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    equivalence.write_text('{"equivalence_pass": false}', encoding="utf-8")
    with mock.patch.object(audit, "generate_phase_activity") as generate:
        with pytest.raises(ValueError, match="GQA8 shared-KV equivalence did not pass"):
            _config(tmp_path / "config.json", parallel_query_head_lanes=8)
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

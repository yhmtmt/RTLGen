from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import audit_attention_decode_score_multivalue_service_activity_power as audit
from npu.eval.probe_attention_decode_score_multivalue_integrated_service import _workload_contract


def _scaled_counts(cluster_count: int) -> dict[str, int]:
    return {
        "request_count": 48 * int(cluster_count),
        "wide_response_count": 48 * int(cluster_count),
        "result_count": 16 * int(cluster_count),
    }


def _config(path: Path, *, cluster_count: int = 1) -> None:
    top_name = (
        "attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_macro_activity"
        if cluster_count == 2
        else "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_macro_activity"
    )
    path.write_text(
        json.dumps(
            {
                "top_name": top_name,
                "attention_decode_score_multivalue_service": {
                    "cluster_count": cluster_count,
                    "max_blocks": 16,
                    "packet_w": 128,
                    "banks": 4,
                    "req_queue_depth": 4,
                    "resp_queue_depth": 4,
                    "bank_queue_depth": 4,
                    "read_latency": 2,
                    "arb_mode": "round_robin",
                    "locality_burst_max": 2,
                    "score_scale_lanes_per_cycle": 1,
                    "value_memory_backend": "macro_banked_4x16x64x32",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_metrics(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "instance_area_um2",
        "params_json",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _ok_metric(
    *,
    param_hash: str = "p1",
    flow_variant: str = audit._REQUIRED_FLOW_VARIANT,
    design: str = audit._EXPECTED_DESIGN,
    critical_path_ns: str = "9.2",
    die_area: str = "9000000",
    total_power_mw: str = "12.75",
    instance_area_um2: str = "3300000",
    tag: str = "die3000",
) -> dict[str, str]:
    return {
        "design": design,
        "platform": audit._EXPECTED_PLATFORM,
        "config_hash": "cfg1",
        "param_hash": param_hash,
        "tag": tag,
        "status": "ok",
        "critical_path_ns": critical_path_ns,
        "die_area": die_area,
        "total_power_mw": total_power_mw,
        "instance_area_um2": instance_area_um2,
        "params_json": json.dumps({"CLOCK_PERIOD": 10, "FLOW_VARIANT": flow_variant}),
    }


def test_repo_c1_metric_contract_selects_merged_r3_row() -> None:
    metrics = (
        REPO_ROOT
        / "runs/designs/npu_blocks/"
        "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr/metrics.csv"
    )

    row = audit._select_c1_metric(metrics, clock_period_ns=10.0)

    assert row["param_hash"] == "696d01b6"
    assert row["tag"] == (
        "decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1_"
        "macro_conservative_c1_die_3000"
    )
    assert float(row["critical_path_ns"]) == 6.7148


def _cluster_equivalence(path: Path, *, passed: bool = True) -> None:
    path.write_text(
        json.dumps(
            {
                "decision": "decode_score_multivalue_cluster_equivalence_pass",
                "equivalence_pass": passed,
                "score_tensor_hash": "score-hash",
                "final_tensor_hash": "final-hash",
                "semantic_profile": "shared_score_integer_contract",
            }
        ),
        encoding="utf-8",
    )


def _integrated_service(
    path: Path,
    *,
    case_id: str = "c1_p128_b4_rr",
    cluster_count: int = 1,
    exact_match: bool = True,
    include_counters: bool = True,
    cycle_count: int = 321,
) -> None:
    counters = {
        "request_injection_stall_cycles": 0,
        "arbitration_contention_cycles": 1,
        "bank_conflict_count": 2,
        "response_block_cycles": {"router": 0, "service": 0},
        "shared_result": {"arbitration_contention_cycles": 1, "egress_block_cycles": 1},
        "max_occupancy": {"router_req": 1, "router_resp": 1, "service_req": 1, "service_resp": 1},
    }
    if not include_counters:
        counters.pop("max_occupancy")
    counts = _scaled_counts(cluster_count)
    path.write_text(
        json.dumps(
            {
                "workload_contract": _workload_contract(),
                "summary": {
                    "all_hash_gates_passed": True,
                    "all_protocol_gates_passed": True,
                    "all_count_gates_passed": True,
                },
                "cases": [
                    {
                        "case_id": case_id,
                        "decision": "pass",
                        "config": {
                            "cluster_count": cluster_count,
                            "packet_w": 128,
                            "banks": 4,
                            "req_queue_depth": 4,
                            "resp_queue_depth": 4,
                            "bank_queue_depth": 4,
                            "read_latency": 2,
                            "arb_mode": "round_robin",
                            "locality_burst_max": 2,
                        },
                        "integrated_service": {
                            "exact_match": exact_match,
                            "no_protocol_errors": True,
                            "no_drop_duplicate_deadlock_timeout": True,
                            "cycle_bound_ok": True,
                            "request_count": counts["request_count"],
                            "wide_response_count": counts["wide_response_count"],
                            "result_count": counts["result_count"],
                            "completion_cycle": cycle_count,
                            "score_hash": "score-hash",
                            "final_hash": "final-hash",
                            "request_hash": "request-hash",
                            "wide_response_matrix_hash": "wide-hash",
                            "counters": counters,
                            "shared_result_egress": {"documented_initiation_interval": 1},
                        },
                        "gates": {
                            "hash_gate_ok": True,
                            "protocol_gate_ok": True,
                            "count_gate_ok": True,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _generated_activity_manifest(
    *,
    case_id: str = "c1_p128_b4_rr",
    cluster_count: int = 1,
    cycle_count: int = 321,
    score_hash: str = "score-hash",
    final_hash: str = "final-hash",
    request_hash: str = "request-hash",
    wide_hash: str = "wide-hash",
) -> dict:
    counts = _scaled_counts(cluster_count)
    return {
        "model": "attention_decode_score_multivalue_service_activity_v1",
        "case_id": case_id,
        "workload_contract": _workload_contract(),
        "clock_period_ns": 10.0,
        "cycle_count": cycle_count,
        "request_result_protocol_counters": {
            "request_count": counts["request_count"],
            "wide_response_count": counts["wide_response_count"],
            "result_count": counts["result_count"],
            "shared": {"protocol_error": False},
        },
        "value_bank_coverage": {
            "addressed_banks_over_trace": [0, 1, 2],
            "inactive_banks": [3],
            "inactive_reason": "three_block_reference_workload",
        },
        "hashes": {
            "vcd_sha256": "vcd-hash",
            "score_hash": score_hash,
            "final_hash": final_hash,
            "request_hash": request_hash,
            "wide_response_matrix_hash": wide_hash,
        },
    }


def _adapted_manifest(
    tmp_path: Path,
    *,
    cycle_count: int = 321,
    macro_counts: dict[str, int] | None = None,
    score_hash: str = "score-hash",
    final_hash: str = "final-hash",
    request_hash: str = "request-hash",
    wide_hash: str = "wide-hash",
) -> tuple[dict, Path, dict]:
    macro_counts = macro_counts or {"fakeram45_2048x39": 56, "fakeram45_64x32": 64}
    score_instances = int(macro_counts["fakeram45_2048x39"])
    value_instances = int(macro_counts["fakeram45_64x32"])
    manifest = {
        "clock_period_ns": 10.0,
        "phases": [
            {
                "phase": "service_window",
                "vcd": "attention_decode_score_multivalue_service_activity.vcd",
                "vcd_sha256": "vcd-hash",
                "macro_activity": "service_macro_activity.json",
                "macro_activity_sha256": "macro-sidecar-hash",
                "sequential_register_activity": "service_seq_activity.json",
                "sequential_register_activity_sha256": "seq-sidecar-hash",
                "measured_cycles": cycle_count,
                "full_context_cycles": cycle_count,
                "requires_macro_activity": True,
            }
        ],
    }
    manifest_path = tmp_path / "attention_decode_score_multivalue_service_postroute_power_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest, manifest_path, {
        "generated_activity_manifest_sha256": "generated-manifest-hash",
        "adapted_activity_manifest_sha256": audit._sha256_file(manifest_path),
        "vcd_sha256": "vcd-hash",
        "cycle_count": cycle_count,
        "generated_manifest_hashes": {
            "vcd_sha256": "vcd-hash",
            "score_hash": score_hash,
            "final_hash": final_hash,
            "request_hash": request_hash,
            "wide_response_matrix_hash": wide_hash,
        },
        "workload_contract": _workload_contract(),
        "macro_counts": dict(macro_counts),
        "macro_activity_contract": {
            "profile": "multivalue_service_c1_v1",
            "total_assignment_count": score_instances * 91 + value_instances * 72,
            "macro_classes": {
                "fakeram45_2048x39": {
                    "instance_scope_prefix": "score_bank",
                    "instance_count": score_instances,
                    "pins_per_instance": 91,
                    "assignment_count": score_instances * 91,
                },
                "fakeram45_64x32": {
                    "instance_scope_prefix": "gen_value_macro_backend",
                    "instance_count": value_instances,
                    "pins_per_instance": 72,
                    "assignment_count": value_instances * 72,
                },
            },
        },
        "bank_coverage": {"inactive_banks": [3]},
    }


def _power_report(
    *,
    manifest_sha256: str,
    with_abs_path: bool = False,
    cycle_count: int = 321,
    macro_activity_assignment_count: int = 9704,
) -> dict:
    phase = {
        "phase": "service_window",
        "vcd": "/tmp/private/activity.vcd" if with_abs_path else "attention_decode_score_multivalue_service_activity.vcd",
        "vcd_sha256": "vcd-hash",
        "measured_cycles": cycle_count,
        "full_context_cycles": cycle_count,
        "annotation_gate_pass": True,
        "macro_activity_gate_pass": True,
        "structural_macro_activity_gate_pass": True,
        "sequential_register_activity_gate_pass": True,
        "clock_period_gate_pass": True,
        "macro_activity_assignment_count": macro_activity_assignment_count,
        "power": {
            "internal_w": 0.10,
            "switching_w": 0.20,
            "leakage_w": 0.05,
            "total_w": 0.35,
        },
    }
    return {
        "model": "postroute_phase_vcd_power_v1",
        "status": "activity_backed",
        "promotion_gate_pass": True,
        "clock_period_ns": 10.0,
        "source_activity_manifest": "<evaluator-local-path>/attention_decode_score_multivalue_service_postroute_power_manifest.json",
        "source_activity_manifest_sha256": manifest_sha256,
        "phases": [phase],
    }


def test_select_c1_metric_rejects_ambiguity_and_flow_mismatch(tmp_path: Path) -> None:
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, [_ok_metric(flow_variant="wrong_variant")])
    with pytest.raises(ValueError, match="expected exactly one"):
        audit._select_c1_metric(metrics, clock_period_ns=10.0)

    _write_metrics(metrics, [_ok_metric(param_hash="p1"), _ok_metric(param_hash="p2")])
    with pytest.raises(ValueError, match="found 2"):
        audit._select_c1_metric(metrics, clock_period_ns=10.0)

    wrong_design = _ok_metric()
    wrong_design["design"] = "other_design"
    _write_metrics(metrics, [wrong_design])
    with pytest.raises(ValueError, match="design"):
        audit._select_c1_metric(metrics, clock_period_ns=10.0)


def test_dependency_gates_reject_weak_equivalence_or_protocol(tmp_path: Path) -> None:
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence, passed=False)
    with pytest.raises(ValueError, match="merged cluster equivalence did not pass"):
        audit._validate_cluster_equivalence(audit._load(equivalence))

    integrated = tmp_path / "integrated.json"
    _integrated_service(integrated, exact_match=False)
    with pytest.raises(ValueError, match="exact_result_match gate failed"):
        audit._validate_integrated_service(audit._load(integrated))

    _integrated_service(integrated, include_counters=False)
    with pytest.raises(ValueError, match="counters incomplete"):
        audit._validate_integrated_service(audit._load(integrated))


def test_validate_generated_activity_manifest_and_macro_counts(tmp_path: Path) -> None:
    activity_manifest_path = tmp_path / audit._OUTPUT_MANIFEST_NAME
    activity_manifest_path.write_text(
        json.dumps(_generated_activity_manifest(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    macro_manifest = {
        "manifest_params": {
            "score_bank_macro_count": 56,
            "value_memory_macro_count": 64,
        }
    }
    assert audit._validate_generated_activity_manifest(_generated_activity_manifest(), tmp_path)[
        "cycle_count"
    ] == 321
    assert audit._validate_macro_manifest_counts(macro_manifest) == {
        "fakeram45_2048x39": 56,
        "fakeram45_64x32": 64,
    }
    macro_manifest["manifest_params"]["value_memory_macro_count"] = 63
    with pytest.raises(ValueError, match="value-memory macro count mismatch"):
        audit._validate_macro_manifest_counts(macro_manifest)


def test_build_report_success_keeps_paths_portable_and_writes_markdown(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _config(config)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, [_ok_metric()])
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    integrated = tmp_path / "integrated.json"
    _integrated_service(integrated)
    physical_signoff = tmp_path / "physical_signoff.json"
    physical_signoff.write_text(
        json.dumps(
            {
                "version": 1,
                "status": "routed_with_electrical_caveat",
                "source_item_id": "source-pnr-r3",
                "source_pr": 1548,
                "source_url": "https://github.com/yhmtmt/RTLGen/pull/1548",
                "architectural_use": "exploratory_routed_ppa_not_electrical_signoff",
                "metric_identity": {
                    "design": audit._EXPECTED_DESIGN,
                    "platform": audit._EXPECTED_PLATFORM,
                    "param_hash": "p1",
                    "tag": "die3000",
                },
                "route_checks": {
                    "drc_violations": 0,
                    "setup_violations": 0,
                    "hold_violations": 0,
                    "max_slew_violations": 0,
                    "max_cap_violations": 142,
                    "worst_max_cap_slack_ff": -17.81,
                    "max_cap_limit_ff": 60.65,
                },
            }
        ),
        encoding="utf-8",
    )
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(tmp_path)

    with mock.patch.object(audit, "generate_activity", return_value=_generated_activity_manifest()), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta),
    ), mock.patch.object(
        audit,
        "build_power_report",
        return_value=_power_report(manifest_sha256=adapted_meta["adapted_activity_manifest_sha256"], with_abs_path=False),
    ):
        payload = audit.build_report(
            config=config,
            c1_metrics_csv=metrics,
            equivalence_json=equivalence,
            integrated_service_json=integrated,
            orfs_design_config=Path("/orfs/flow/designs/nangate45/service/config.mk"),
            clock_period_ns=10.0,
            activity_dir=tmp_path / "activity",
            physical_signoff_json=physical_signoff,
        )

    assert payload["decision"] == "activity_backed_service_power_measured"
    assert payload["promotion_gate_pass"] is True
    best = payload["best"]
    assert best["status"] == "activity_backed"
    assert best["authoritative_composed_c1_total_ppa"]["total_power_mw"] == 12.75
    assert best["component_service_window_energy"]["energy_j"]["dynamic"] == pytest.approx(0.30 * 321e-9 * 10.0)
    assert best["component_service_window_energy"]["energy_j"]["leakage"] == pytest.approx(0.05 * 321e-9 * 10.0)
    assert payload["bank3_dynamic_inactivity"]["inactive_banks"] == [3]
    assert payload["dependency_contract"]["integrated_service_c1"]["config"]["cluster_count"] == 1
    assert payload["activity_contract"]["workload_contract"] == _workload_contract()
    assert payload["physical_signoff"]["status"] == "routed_with_electrical_caveat"
    assert payload["physical_signoff"]["route_checks"]["max_cap_violations"] == 142
    assert payload["physical_signoff"]["route_checks"]["worst_max_cap_slack_ff"] == -17.81
    assert payload["physical_signoff"]["architectural_use"] == (
        "exploratory_routed_ppa_not_electrical_signoff"
    )
    assert "/tmp/" not in json.dumps(payload, sort_keys=True)
    assert "/orfs/" not in json.dumps(payload, sort_keys=True)

    markdown_path = tmp_path / "report.md"
    audit._write_markdown(payload, markdown_path)
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "bank3 dynamic inactivity" in markdown
    assert "service-window dynamic J" in markdown
    assert "maximum-capacitance violations: `142`" in markdown
    assert "exploratory_routed_ppa_not_electrical_signoff" in markdown


def test_build_report_marks_openroad_failure_as_measurement_failed(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _config(config)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, [_ok_metric()])
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    integrated = tmp_path / "integrated.json"
    _integrated_service(integrated)
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(tmp_path)

    with mock.patch.object(audit, "generate_activity", return_value=_generated_activity_manifest()), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta),
    ), mock.patch.object(
        audit,
        "build_power_report",
        side_effect=RuntimeError("/orfs/private/run/6_final.odb failed after /tmp/work/vcd"),
    ):
        payload = audit.build_report(
            config=config,
            c1_metrics_csv=metrics,
            equivalence_json=equivalence,
            integrated_service_json=integrated,
            orfs_design_config=Path("/orfs/flow/designs/nangate45/service/config.mk"),
            clock_period_ns=10.0,
            activity_dir=tmp_path / "activity",
        )

    assert payload["promotion_gate_pass"] is False
    assert payload["candidates"][0]["status"] == "measurement_failed"
    assert "/orfs/" not in json.dumps(payload["candidates"][0], sort_keys=True)
    assert "/tmp/" not in json.dumps(payload["candidates"][0], sort_keys=True)


def test_build_report_rejects_non_positive_power_components(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _config(config)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, [_ok_metric()])
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    integrated = tmp_path / "integrated.json"
    _integrated_service(integrated)
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(tmp_path)
    bad_report = _power_report(manifest_sha256=adapted_meta["adapted_activity_manifest_sha256"])
    bad_report["phases"][0]["power"]["leakage_w"] = 0.0
    bad_report["phases"][0]["power"]["total_w"] = 0.30

    with mock.patch.object(audit, "generate_activity", return_value=_generated_activity_manifest()), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta),
    ), mock.patch.object(audit, "build_power_report", return_value=bad_report):
        payload = audit.build_report(
            config=config,
            c1_metrics_csv=metrics,
            equivalence_json=equivalence,
            integrated_service_json=integrated,
            orfs_design_config=Path("/orfs/flow/designs/nangate45/service/config.mk"),
            clock_period_ns=10.0,
            activity_dir=tmp_path / "activity",
        )

    assert payload["promotion_gate_pass"] is False
    assert payload["candidates"][0]["status"] == "rejected_gate"
    assert "finite positive number" in payload["candidates"][0]["failure"]["error_summary"]


def test_validate_generated_activity_manifest_rejects_128_as_active_context(tmp_path: Path) -> None:
    payload = _generated_activity_manifest()
    payload["workload_contract"]["active_context_tokens"] = 128
    (tmp_path / audit._OUTPUT_MANIFEST_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="workload contract mismatch"):
        audit._validate_generated_activity_manifest(payload, tmp_path)


def test_build_report_rejects_generated_activity_hash_mismatch(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _config(config)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, [_ok_metric()])
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    integrated = tmp_path / "integrated.json"
    _integrated_service(integrated)
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(tmp_path)
    generated = _generated_activity_manifest()
    generated["hashes"]["request_hash"] = "wrong-request-hash"

    with mock.patch.object(audit, "generate_activity", return_value=generated), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta | {"generated_manifest_hashes": generated["hashes"], "workload_contract": _workload_contract()}),
    ), mock.patch.object(
        audit,
        "build_power_report",
        return_value=_power_report(manifest_sha256=adapted_meta["adapted_activity_manifest_sha256"], with_abs_path=False),
    ) as build_power_report_mock:
        with pytest.raises(ValueError, match="generated activity request_hash does not match integrated-service c1 request_hash"):
            audit.build_report(
                config=config,
                c1_metrics_csv=metrics,
                equivalence_json=equivalence,
                integrated_service_json=integrated,
                orfs_design_config=Path("/orfs/flow/designs/nangate45/service/config.mk"),
                clock_period_ns=10.0,
                activity_dir=tmp_path / "activity",
            )
    build_power_report_mock.assert_not_called()


def test_build_report_does_not_compare_integrated_hashes_to_cluster_equivalence_hashes(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _config(config)
    metrics = tmp_path / "metrics.csv"
    _write_metrics(metrics, [_ok_metric()])
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    eq_payload = json.loads(equivalence.read_text(encoding="utf-8"))
    eq_payload["score_tensor_hash"] = "different-score-hash"
    eq_payload["final_tensor_hash"] = "different-final-hash"
    equivalence.write_text(json.dumps(eq_payload), encoding="utf-8")
    integrated = tmp_path / "integrated.json"
    _integrated_service(integrated)
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(tmp_path)

    with mock.patch.object(audit, "generate_activity", return_value=_generated_activity_manifest()), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta | {"workload_contract": _workload_contract()}),
    ), mock.patch.object(
        audit,
        "build_power_report",
        return_value=_power_report(manifest_sha256=adapted_meta["adapted_activity_manifest_sha256"], with_abs_path=False),
    ):
        payload = audit.build_report(
            config=config,
            c1_metrics_csv=metrics,
            equivalence_json=equivalence,
            integrated_service_json=integrated,
            orfs_design_config=Path("/orfs/flow/designs/nangate45/service/config.mk"),
            clock_period_ns=10.0,
            activity_dir=tmp_path / "activity",
        )

    assert payload["promotion_gate_pass"] is True


def test_build_report_supports_c2_case_and_validates_cycle_contract_before_power(tmp_path: Path) -> None:
    config = tmp_path / "config_c2.json"
    _config(config, cluster_count=2)
    metrics = tmp_path / "metrics_c2.csv"
    _write_metrics(
        metrics,
        [
            _ok_metric(
                flow_variant="decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                design="attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
                critical_path_ns="9.7",
                die_area="13690000",
                total_power_mw="18.1",
                instance_area_um2="4500000",
                tag="die3700",
            )
        ],
    )
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    integrated = tmp_path / "integrated_c2.json"
    _integrated_service(
        integrated,
        case_id="c2_p128_b4_rr",
        cluster_count=2,
        cycle_count=8863,
    )
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(
        tmp_path,
        cycle_count=8863,
        macro_counts={"fakeram45_2048x39": 112, "fakeram45_64x32": 64},
    )

    with mock.patch.object(
        audit,
        "generate_activity",
        return_value=_generated_activity_manifest(case_id="c2_p128_b4_rr", cluster_count=2, cycle_count=8863),
    ), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta),
    ), mock.patch.object(
        audit,
        "build_power_report",
        return_value=_power_report(
            manifest_sha256=adapted_meta["adapted_activity_manifest_sha256"],
            with_abs_path=False,
            cycle_count=8863,
            macro_activity_assignment_count=14800,
        ),
    ):
        payload = audit.build_report(
            config=config,
            metrics_csv=metrics,
            case_id="c2_p128_b4_rr",
            equivalence_json=equivalence,
            integrated_service_json=integrated,
            orfs_design_config=Path("/orfs/flow/designs/nangate45/service_c2/config.mk"),
            clock_period_ns=10.0,
            activity_dir=tmp_path / "activity_c2",
        )

    assert payload["promotion_gate_pass"] is True
    assert payload["selection_contract"]["case_id"] == "c2_p128_b4_rr"
    assert payload["selection_contract"]["cluster_count"] == 2
    assert payload["dependency_contract"]["integrated_service_c2"]["case_id"] == "c2_p128_b4_rr"
    assert payload["activity_contract"]["cycle_count"] == 8863
    assert payload["best"]["authoritative_composed_c2_total_ppa"]["instance_area_um2"] == 4_500_000
    assert payload["macro_manifest_contract"]["counts"]["fakeram45_2048x39"] == 112


def test_build_report_rejects_c2_hash_mismatch_before_power(tmp_path: Path) -> None:
    config = tmp_path / "config_c2.json"
    _config(config, cluster_count=2)
    metrics = tmp_path / "metrics_c2.csv"
    _write_metrics(
        metrics,
        [
            _ok_metric(
                flow_variant="decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr_3700_v1",
                design="attention_decode_score_multivalue_service_c2_p128_b4_q4_rl2_rr",
                critical_path_ns="9.7",
                die_area="13690000",
                total_power_mw="18.1",
                instance_area_um2="4500000",
                tag="die3700",
            )
        ],
    )
    equivalence = tmp_path / "equivalence.json"
    _cluster_equivalence(equivalence)
    integrated = tmp_path / "integrated_c2.json"
    _integrated_service(
        integrated,
        case_id="c2_p128_b4_rr",
        cluster_count=2,
        cycle_count=8863,
    )
    generated = _generated_activity_manifest(
        case_id="c2_p128_b4_rr",
        cluster_count=2,
        cycle_count=8863,
        request_hash="wrong-request-hash",
    )
    adapted_manifest, manifest_path, adapted_meta = _adapted_manifest(
        tmp_path,
        cycle_count=8863,
        macro_counts={"fakeram45_2048x39": 112, "fakeram45_64x32": 64},
        request_hash="wrong-request-hash",
    )

    with mock.patch.object(audit, "generate_activity", return_value=generated), mock.patch.object(
        audit,
        "_prepare_postroute_power_manifest",
        return_value=(adapted_manifest, manifest_path, adapted_meta),
    ), mock.patch.object(audit, "build_power_report") as build_power_report_mock:
        with pytest.raises(
            ValueError,
            match="generated activity request_hash does not match integrated-service c2_p128_b4_rr request_hash",
        ):
            audit.build_report(
                config=config,
                metrics_csv=metrics,
                case_id="c2_p128_b4_rr",
                equivalence_json=equivalence,
                integrated_service_json=integrated,
                orfs_design_config=Path("/orfs/flow/designs/nangate45/service_c2/config.mk"),
                clock_period_ns=10.0,
                activity_dir=tmp_path / "activity_c2",
            )
    build_power_report_mock.assert_not_called()

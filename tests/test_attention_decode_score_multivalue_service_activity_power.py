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


def _config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "top_name": "attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_macro_activity",
                "attention_decode_score_multivalue_service": {
                    "cluster_count": 1,
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


def _ok_metric(*, param_hash: str = "p1", flow_variant: str = audit._REQUIRED_FLOW_VARIANT) -> dict[str, str]:
    return {
        "design": audit._EXPECTED_DESIGN,
        "platform": audit._EXPECTED_PLATFORM,
        "config_hash": "cfg1",
        "param_hash": param_hash,
        "tag": "die3000",
        "status": "ok",
        "critical_path_ns": "9.2",
        "die_area": "9000000",
        "total_power_mw": "12.75",
        "instance_area_um2": "3300000",
        "params_json": json.dumps({"CLOCK_PERIOD": 10, "FLOW_VARIANT": flow_variant}),
    }


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


def _integrated_service(path: Path, *, exact_match: bool = True, include_counters: bool = True) -> None:
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
                        "case_id": "c1_p128_b4_rr",
                        "decision": "pass",
                        "config": {
                            "cluster_count": 1,
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
                            "request_count": 48,
                            "wide_response_count": 48,
                            "result_count": 16,
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


def _generated_activity_manifest() -> dict:
    return {
        "model": "attention_decode_score_multivalue_service_activity_v1",
        "case_id": "c1_p128_b4_rr",
        "workload_contract": _workload_contract(),
        "clock_period_ns": 10.0,
        "cycle_count": 321,
        "request_result_protocol_counters": {
            "request_count": 48,
            "wide_response_count": 48,
            "result_count": 16,
            "shared": {"protocol_error": False},
        },
        "value_bank_coverage": {
            "addressed_banks_over_trace": [0, 1, 2],
            "inactive_banks": [3],
            "inactive_reason": "three_block_reference_workload",
        },
        "hashes": {
            "vcd_sha256": "vcd-hash",
            "score_hash": "score-hash",
            "final_hash": "final-hash",
            "request_hash": "request-hash",
            "wide_response_matrix_hash": "wide-hash",
        },
    }


def _adapted_manifest(tmp_path: Path) -> tuple[dict, Path, dict]:
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
                "measured_cycles": 321,
                "full_context_cycles": 321,
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
        "cycle_count": 321,
        "generated_manifest_hashes": {
            "vcd_sha256": "vcd-hash",
            "score_hash": "score-hash",
            "final_hash": "final-hash",
            "request_hash": "request-hash",
            "wide_response_matrix_hash": "wide-hash",
        },
        "workload_contract": _workload_contract(),
        "macro_counts": {"fakeram45_2048x39": 56, "fakeram45_64x32": 64},
        "macro_activity_contract": {
            "profile": "multivalue_service_c1_v1",
            "total_assignment_count": 9704,
            "macro_classes": {
                "fakeram45_2048x39": {
                    "instance_scope_prefix": "score_bank",
                    "instance_count": 56,
                    "pins_per_instance": 91,
                    "assignment_count": 5096,
                },
                "fakeram45_64x32": {
                    "instance_scope_prefix": "gen_value_macro_backend",
                    "instance_count": 64,
                    "pins_per_instance": 72,
                    "assignment_count": 4608,
                },
            },
        },
        "bank_coverage": {"inactive_banks": [3]},
    }


def _power_report(*, manifest_sha256: str, with_abs_path: bool = False) -> dict:
    phase = {
        "phase": "service_window",
        "vcd": "/tmp/private/activity.vcd" if with_abs_path else "attention_decode_score_multivalue_service_activity.vcd",
        "vcd_sha256": "vcd-hash",
        "measured_cycles": 321,
        "full_context_cycles": 321,
        "annotation_gate_pass": True,
        "macro_activity_gate_pass": True,
        "structural_macro_activity_gate_pass": True,
        "sequential_register_activity_gate_pass": True,
        "clock_period_gate_pass": True,
        "macro_activity_assignment_count": 9704,
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
    assert "/tmp/" not in json.dumps(payload, sort_keys=True)
    assert "/orfs/" not in json.dumps(payload, sort_keys=True)

    markdown_path = tmp_path / "report.md"
    audit._write_markdown(payload, markdown_path)
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "bank3 dynamic inactivity" in markdown
    assert "service-window dynamic J" in markdown


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

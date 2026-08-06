import csv
import json
from pathlib import Path
import sys
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval import audit_llm_decoder_attention_score32_schedule_wrapper_postroute_activity_power as audit


def _write_metrics(path: Path) -> None:
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
        writer.writerow(
            {
                "design": "attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2",
                "platform": "nangate45",
                "config_hash": "cfg",
                "param_hash": "p0",
                "tag": "density04",
                "status": "ok",
                "critical_path_ns": "48.6509",
                "die_area": "0",
                "total_power_mw": "60.7",
                "instance_area_um2": "693452.0",
                "params_json": json.dumps(
                    {
                        "FLOW_VARIANT": "attention_dual_stream_schedule_wrapper_score32_exp_lut",
                        "CLOCK_PERIOD": 10.0,
                        "PLACE_DENSITY": 0.4,
                    }
                ),
            }
        )


def _write_recost(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "diagnosis": {"decision": "dual_stream_feasible"},
                "best_requested": {
                    "substituted_compute_arch": "attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2",
                    "substituted_compute_variant_kind": "dual_stream_schedule_wrapper",
                    "substituted_compute_semantic_profile": "score32_exp_lut_div",
                    "replica_recost_area_fit_replica_count": 428,
                    "replica_recost_tile_service_cycles": 986,
                    "tile_service_cycles": 986,
                    "tile_waves": 8,
                    "layers": 32,
                    "replica_recost_qkv_cycles": 192,
                    "cross_tile_reduction_cycles": 141,
                    "kv_write_cycles": 10,
                    "replica_recost_layer_cycles": 8231,
                    "replica_recost_latency_us": 12814.257853,
                    "replica_recost_compute_area_um2": 693452.0 * 428,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "top_name": "attention_dual_stream_schedule_wrapper_score32_exp_lut_8x8_c2",
                "attention_dual_stream_schedule_wrapper": {
                    "clusters": 2,
                    "queue_depth": 16,
                    "tile_id_bits": 16,
                    "wave_id_bits": 12,
                    "base_token_bits": 18,
                    "max_inflight_per_cluster": 2,
                    "cluster_service_cycles": 4,
                    "datapath": {
                        "streams": 2,
                        "array_m": 8,
                        "array_n": 8,
                        "k_unroll": 1,
                        "mac_accum_bits": 32,
                        "softmax_row_elems": 8,
                        "softmax_score_bits": 32,
                        "softmax_weight_bits": 16,
                        "softmax_input_frac_bits": 28,
                        "softmax_accum_bits": 40,
                        "reciprocal_bits": 16,
                        "softmax_reciprocal_lut_bucket_shift": 20,
                        "value_bits": 8,
                        "value_lanes": 8,
                        "partials": 8,
                        "partials_per_cycle": 1,
                        "stream_buffer_bits": 512,
                        "equivalence_hash": False,
                        "softmax_pipeline_stages": 1,
                        "softmax_impl": "exp_lut_div",
                        "semantic_profile": "score32_exp_lut_div",
                    },
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _activity_manifest(*, cycle_count: int) -> dict:
    return {
        "model": "attention_dual_stream_schedule_wrapper_activity_v1",
        "cycle_count": cycle_count,
        "service_window_cycles": cycle_count,
        "cluster_service_cycles": 4,
        "hashes": {"vcd_sha256": "vcd-hash"},
        "gates": {
            "equivalence_pass": True,
            "protocol_gate_ok": True,
            "count_gate_ok": True,
            "hash_gate_ok": True,
            "observable_completion_gate_ok": True,
            "window_active_gate_ok": True,
            "both_clusters_issue_gate_ok": True,
            "service_window_gate_ok": True,
        },
        "request_result_protocol_counters": {
            "window_active_cycles": cycle_count,
            "window_issue_counts": {"0": 165, "1": 164},
        },
    }


def _power_report() -> dict:
    return {
        "status": "activity_backed",
        "promotion_gate_pass": True,
        "source_activity_manifest_sha256": "manifest-hash",
        "phases": [
            {
                "phase": "service_window",
                "vcd_sha256": "vcd-hash",
                "measured_cycles": 986,
                "full_context_cycles": 986,
                "macro_activity_assignment_count": 0,
                "annotation_gate_pass": True,
                "sequential_register_activity_gate_pass": True,
                "clock_period_gate_pass": True,
                "power_numeric_gate_pass": True,
                "structural_macro_activity_gate_pass": True,
                "phase_gate_pass": True,
                "power": {
                    "internal_w": 0.2,
                    "switching_w": 0.3,
                    "leakage_w": 0.1,
                    "total_w": 0.6,
                },
            }
        ],
    }


def test_service_window_power_accepts_independent_report_rounding() -> None:
    report = _power_report()
    report["phases"][0]["power"] = {
        "internal_w": 0.153530582786,
        "switching_w": 0.0866372808814,
        "leakage_w": 0.116741158068,
        "total_w": 0.356909006834,
    }

    measured = audit._strict_service_window_measurement(
        activity_power=report,
        manifest_sha256="manifest-hash",
        expected_vcd_sha256="vcd-hash",
        expected_cycle_count=986,
        authoritative_critical_path_ns=48.6509,
    )

    assert measured["power_w"]["total"] == pytest.approx(0.356909006834)


def test_service_window_power_rejects_material_component_mismatch() -> None:
    report = _power_report()
    report["phases"][0]["power"]["total_w"] = 0.59

    with pytest.raises(ValueError, match="total_w does not match"):
        audit._strict_service_window_measurement(
            activity_power=report,
            manifest_sha256="manifest-hash",
            expected_vcd_sha256="vcd-hash",
            expected_cycle_count=986,
            authoritative_critical_path_ns=48.6509,
        )


def test_build_report_rejects_accidental_4_cycle_scaling(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    metrics = tmp_path / "metrics.csv"
    recost = tmp_path / "recost.json"
    _write_config(config)
    _write_metrics(metrics)
    _write_recost(recost)

    with mock.patch.object(audit, "generate_activity", return_value=_activity_manifest(cycle_count=4)):
        with pytest.raises(ValueError, match="service_window_cycles mismatch"):
            audit.build_report(
                config=config,
                metrics_csv=metrics,
                recost_json=recost,
                orfs_design_config=tmp_path / "orfs_config.mk",
                activity_dir=tmp_path / "activity",
            )


def test_build_report_distinguishes_annotation_and_promotion_clocks(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    metrics = tmp_path / "metrics.csv"
    recost = tmp_path / "recost.json"
    _write_config(config)
    _write_metrics(metrics)
    _write_recost(recost)
    manifest_path = tmp_path / "activity_manifest.json"
    manifest_path.write_text("{}\n", encoding="utf-8")

    with mock.patch.object(audit, "generate_activity", return_value=_activity_manifest(cycle_count=986)):
        with mock.patch.object(
            audit,
            "_prepare_postroute_manifest",
            return_value=({"phases": []}, manifest_path),
        ):
            with mock.patch.object(audit, "_sha256_file", return_value="manifest-hash"):
                with mock.patch.object(audit, "build_power_report", return_value=_power_report()):
                    payload = audit.build_report(
                        config=config,
                        metrics_csv=metrics,
                        recost_json=recost,
                        orfs_design_config=tmp_path / "orfs_config.mk",
                        activity_dir=tmp_path / "activity",
                    )

    energy = payload["best"]["component_service_window_energy"]
    assert energy["annotation_clock_ns"] == 10.0
    assert energy["promotion_clock_ns"] == 48.6509
    assert energy["energy_j"]["dynamic"] == pytest.approx((0.2 + 0.3) * 986 * 10.0e-9)
    assert energy["energy_j"]["leakage"] == pytest.approx(0.1 * 986 * 48.6509e-9)
    assert payload["recost_contract"]["residual_layer_cycles"] == 343

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

from npu.eval.audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure import (
    build_report,
)


PHASE2_REL = (
    "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    "decoder_attention_score32_noc_phase2_schedule__"
    "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1.json"
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _phase2_payload(*, noc_clock_ns: float = 1.0, coverage: str = "workload_complete") -> dict:
    return {
        "version": 2,
        "model": "llama7b_proxy",
        "profile": "decoder_attention_score32_noc_phase2_schedule",
        "source_contract": {
            "coverage": coverage,
            "active_clusters": 8,
            "cluster_count": 16,
            "declared_tile_waves": 8,
            "simulated_wave_count": 8,
            "compute_clock_ns": 48.6509,
            "noc_clock_ns": noc_clock_ns,
            "compute_layer_time_ns": 421511.3976,
        },
        "mapping": {
            "cluster_endpoints": [0, 1, 2, 3, 4, 5, 6, 7],
            "root_endpoint": 15,
        },
        "traffic_quantities": {
            "tile_count": 128,
            "simulated_tiles": 128,
            "shared_tile_payload_bytes": 8192,
            "partial_reduction_payload_bytes": 1024,
        },
        "schedule_parameters": {
            "wave_start_compute_cycles": [192, 1178],
            "wave_start_noc_cycles": [9341, 57311],
            "reduction_release_compute_cycles": [1178, 2164],
            "reduction_release_noc_cycles": [57311, 105281],
            "compute_to_noc_clock_ratio": 48.6509,
            "release_conversion": "ceil(compute_cycles * compute_clock_ns / noc_clock_ns)",
        },
        "simulation": {
            "cycles_to_drain": 397004,
            "drain_time_ns": 397004.0,
            "drain_within_source_compute_layer_envelope": True,
            "drain_minus_compute_layer_time_ns": -24507.3976,
            "scheduled_packet_count": 512,
            "scheduled_flit_count": 92128,
            "router_contention_cycles": 36747,
            "endpoint_input_stall_cycles_total": 319772,
        },
    }


def _phase1_payload(*, critical_path_ns: float = 1.4, area_um2: float = 12345.0, power_mw: float = 0.42) -> dict:
    return {
        "item_id": "l1_segmented_xy_mesh_noc_phase1_v1_r7",
        "task_type": "l1_sweep",
        "evaluation_record": {
            "evaluation_mode": "measurement_only",
            "physical_metrics_present": True,
            "timing_feasible": True,
            "clock_period_ns": 1.0,
            "timing_slack_ns": 0.1,
        },
        "proposals": [
            {
                "metrics_ref": {
                    "metrics_csv": "runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/metrics.csv",
                    "param_hash": "abcd1234",
                    "tag": "segmented_router_anchor",
                    "result_path": "runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/work/abcd1234/result.json",
                    "work_result_json": "runs/designs/noc/l1_noc_segmented_xy_router_p5_w256_vc4_d4_wrapper/work/abcd1234/result.json",
                },
                "metric_summary": {
                    "critical_path_ns": critical_path_ns,
                    "die_area": area_um2,
                    "total_power_mw": power_mw,
                },
            }
        ],
    }


def _args(repo_root: Path, *, phase2_rel: str, phase1_rel: str) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=repo_root,
        phase2_schedule_json=Path(phase2_rel),
        phase1_router_promotion_json=Path(phase1_rel),
        json_out=repo_root / "out.json",
        report_out=repo_root / "out.md",
    )


def test_measured_router_closure_uses_conservative_slower_router_clock_and_labels_component_sum(
    tmp_path: Path,
) -> None:
    phase2_rel = PHASE2_REL
    phase1_rel = "control_plane/shadow_exports/l1_promotions/l1_segmented_xy_mesh_noc_phase1_v1_r7.json"
    _write_json(tmp_path / phase2_rel, _phase2_payload(noc_clock_ns=1.0))
    _write_json(tmp_path / phase1_rel, _phase1_payload(critical_path_ns=1.4, area_um2=12345.0, power_mw=0.42))

    report = build_report(_args(tmp_path, phase2_rel=phase2_rel, phase1_rel=phase1_rel))

    assert report["profile"] == "decoder_attention_score32_noc_phase2_measured_router_closure"
    assert report["source_items"]["phase2_schedule"] == "l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1"
    assert report["conservative_recost"]["effective_noc_clock_ns"] == pytest.approx(1.4)
    assert report["conservative_recost"]["method"] == "no_reroute_absolute_cycle_upper_bound"
    assert report["conservative_recost"]["no_reroute_upper_bound_drain_time_ns"] == pytest.approx(397004 * 1.4)
    assert report["closure_diagnosis"]["clock_envelope"] == "measured_router_clock_exceeds_source_compute_envelope"
    assert report["router_component_accounting"]["router_count"] == 16
    assert report["router_component_accounting"]["area_um2_lower_bound"] == pytest.approx(16 * 12345.0)
    assert report["router_component_accounting"]["power_mw_component_sum_estimate"] == pytest.approx(16 * 0.42)
    assert report["router_component_accounting"]["power_bound_status"] == (
        "not_a_bound_without_workload_matched_router_activity"
    )
    assert "not aggregate placed-mesh PPA" in report["router_component_accounting"]["label"]
    assert any("Aggregate 4x4 mesh wiring" in item for item in report["remaining_abstractions"])


def test_measured_router_closure_does_not_improve_the_schedule_clock_when_router_is_faster(tmp_path: Path) -> None:
    phase2_rel = PHASE2_REL
    phase1_rel = "phase1.json"
    _write_json(tmp_path / phase2_rel, _phase2_payload(noc_clock_ns=1.0))
    _write_json(tmp_path / phase1_rel, _phase1_payload(critical_path_ns=0.72))

    report = build_report(_args(tmp_path, phase2_rel=phase2_rel, phase1_rel=phase1_rel))

    assert report["conservative_recost"]["effective_noc_clock_ns"] == pytest.approx(1.0)
    assert report["conservative_recost"]["no_reroute_upper_bound_drain_time_ns"] == pytest.approx(397004.0)
    assert report["closure_diagnosis"]["clock_envelope"] == "measured_router_clock_preserves_source_compute_envelope"


def test_measured_router_closure_rejects_superseded_base_router_promotion(tmp_path: Path) -> None:
    phase1 = _phase1_payload()
    phase1["item_id"] = "l1_segmented_xy_mesh_noc_phase1_v1"
    _write_json(tmp_path / PHASE2_REL, _phase2_payload())
    _write_json(tmp_path / "phase1.json", phase1)

    with pytest.raises(ValueError, match="phase1 item_id"):
        build_report(_args(tmp_path, phase2_rel=PHASE2_REL, phase1_rel="phase1.json"))


def test_measured_router_closure_rejects_non_workload_complete_phase2(tmp_path: Path) -> None:
    phase2_rel = PHASE2_REL
    phase1_rel = "phase1.json"
    _write_json(tmp_path / phase2_rel, _phase2_payload(coverage="bounded"))
    _write_json(tmp_path / phase1_rel, _phase1_payload())

    with pytest.raises(ValueError, match="phase2 workload coverage"):
        build_report(_args(tmp_path, phase2_rel=phase2_rel, phase1_rel=phase1_rel))


def test_measured_router_closure_script_runs_without_pythonpath(tmp_path: Path) -> None:
    phase2 = tmp_path / PHASE2_REL
    phase1 = tmp_path / "phase1.json"
    json_out = tmp_path / "out" / "report.json"
    md_out = tmp_path / "out" / "report.md"
    _write_json(phase2, _phase2_payload())
    _write_json(phase1, _phase1_payload())

    subprocess.run(
        [
            sys.executable,
            "npu/eval/audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure.py",
            "--repo-root",
            str(tmp_path),
            "--phase2-schedule-json",
            phase2.relative_to(tmp_path).as_posix(),
            "--phase1-router-promotion-json",
            phase1.relative_to(tmp_path).as_posix(),
            "--json-out",
            str(json_out),
            "--report-out",
            str(md_out),
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
    )

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["decision"] == "score32_noc_phase2_measured_router_closure_recorded"
    assert md_out.exists()


def test_measured_router_closure_rejects_noncanonical_phase2_item(tmp_path: Path) -> None:
    phase2_rel = "phase2.json"
    phase1_rel = "phase1.json"
    _write_json(tmp_path / phase2_rel, _phase2_payload())
    _write_json(tmp_path / phase1_rel, _phase1_payload())

    with pytest.raises(ValueError, match="phase2 item_id"):
        build_report(_args(tmp_path, phase2_rel=phase2_rel, phase1_rel=phase1_rel))


def test_measured_router_closure_rejects_nonpositive_router_metric(tmp_path: Path) -> None:
    phase1_rel = "phase1.json"
    _write_json(tmp_path / PHASE2_REL, _phase2_payload())
    _write_json(tmp_path / phase1_rel, _phase1_payload(power_mw=0.0))

    with pytest.raises(ValueError, match="phase1 total_power_mw must be positive"):
        build_report(_args(tmp_path, phase2_rel=PHASE2_REL, phase1_rel=phase1_rel))

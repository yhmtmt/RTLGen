from argparse import Namespace
import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_score32_integrated_frontier_ranking import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        score32_hbm_dram_service_json=tmp_path / "score32_hbm_service.json",
        score32_measured_command_control_json=tmp_path / "measured_command.json",
        score32_hbm_controller_replay_json=tmp_path / "score32_replay.json",
        score32_hbm_controller_replay_ppa_json=None,
        score32_physical_feasibility_json=None,
        score32_quality_json=tmp_path / "score32_quality.json",
        measured_compute_energy_json=tmp_path / "measured_compute.json",
        mixed_int8_energy_json=tmp_path / "mixed_int8.json",
        integrated_energy_json=tmp_path / "integrated.json",
    )


def _populate_inputs(tmp_path: Path) -> None:
    args = _args(tmp_path)
    _write_json(
        args.score32_hbm_dram_service_json,
        {
            "best_latency": {
                "candidate_id": "score32_exp_lut_hbm_dram_service_closure_best",
                "latency_us": 120,
                "token_throughput_per_s": 8300,
                "compute_energy_mj_per_token": 1.5,
                "hbm_energy_mj_per_token": 0.8,
                "total_energy_mj_per_token": 2.3,
                "die_area_mm2": 2.4,
                "compute_area_mm2": 1.9,
                "macs_per_cycle": 512,
            }
        },
    )
    _write_json(
        args.score32_measured_command_control_json,
        {
            "best_requested": {
                "die_area_mm2": 2.4,
            }
        },
    )
    _write_json(
        args.score32_hbm_controller_replay_json,
        {
            "best_latency": {
                "candidate_id": "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best",
                "latency_us": 100,
                "token_throughput_per_s": 10000,
                "compute_energy_mj_per_token": 1.2,
                "hbm_energy_mj_per_token": 0.7,
                "total_energy_mj_per_token": 1.9,
                "die_area_mm2": 1.7,
                "compute_area_mm2": 1.2,
                "macs_per_cycle": 768,
                "channel_count": 4,
                "remaining_abstractions": [
                    "controller replay is deterministic cycle-level but not RTL-timing accurate",
                    "does not include vendor HBM current signoff",
                ],
            }
        },
    )
    _write_json(
        args.score32_quality_json,
        {
            "decision": {
                "status": "mixed_int8_generation_quality_pass"
            },
            "best_candidate": {
                "decision_status": "mixed_int8_generation_quality_pass",
                "candidate_id": "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best",
            },
        },
    )
    _write_json(
        args.measured_compute_energy_json,
        {
            "best": {
                "candidate_id": "measured_fp16_compute",
                "latency_us": 140,
                "token_throughput_per_s": 7142,
                "energy_mj": 3.0,
                "die_area_mm2": 3.3,
                "compute_area_um2": 2800000,
                "macs_per_cycle": 256,
                "energy_components": {"compute_mj": 1.8, "hbm_mj": 1.2},
            },
        },
    )
    _write_json(
        args.mixed_int8_energy_json,
        {
            "best": {
                "candidate_id": "mixed_int8_energy",
                "latency_us": 160,
                "token_throughput_per_s": 6250,
                "energy_mj": 4.0,
                "die_area_mm2": 2.9,
                "compute_area_um2": 3200000,
                "macs_per_cycle": 256,
                "energy_components": {"compute_mj": 2.5, "hbm_mj": 1.5},
            },
        },
    )
    _write_json(
        args.integrated_energy_json,
        {
            "best": {
                "candidate_id": "integrated",
                "latency_us": 250,
                "token_throughput_per_s": 4000,
                "energy_mj": 5.0,
                "die_area_mm2": 4.0,
                "energy_components": {"compute_mj": 3.0, "hbm_mj": 2.0},
                "compute_area_um2": 1800000,
                "macs_per_cycle": 128,
            },
        },
    )


def test_integrated_frontier_ranking_default_controller_replay_marks_deterministic_abstraction(tmp_path: Path) -> None:
    _populate_inputs(tmp_path)
    args = _args(tmp_path)

    report = build_report(args)

    score32_row = report["rows"][0]
    assert score32_row["candidate_id"] == "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best"
    assert "controller replay is deterministic cycle-level but not RTL-timing accurate" in score32_row[
        "remaining_abstractions"
    ]
    assert score32_row["score32_hbm_controller_replay_ppa"] is None
    assert report["inputs"]["score32_hbm_controller_replay_ppa_json"] is None
    assert any(
        "deterministic cycle-level HBM controller replay." in item for item in report["assumptions"]
    )


def test_integrated_frontier_ranking_with_controller_replay_ppa_marks_rtl_timing_backed(tmp_path: Path) -> None:
    _populate_inputs(tmp_path)
    args = _args(tmp_path)
    args.score32_hbm_controller_replay_ppa_json = tmp_path / "replay_ppa.json"
    _write_json(
        args.score32_hbm_controller_replay_ppa_json,
        {
            "item_id": "l1_decoder_attention_hbm_replay_controller_ppa_v1",
            "proposals": [
                {
                    "metrics_ref": {
                        "metrics_csv": "runs/designs/npu_blocks/attention_hbm_replay_controller_c8/metrics.csv",
                        "status": "ok",
                    },
                    "metric_summary": {
                        "critical_path_ns": 0.37,
                        "die_area": 22222.0,
                        "total_power_mw": 0.03,
                    },
                },
                {
                    "metrics_ref": {
                        "metrics_csv": "runs/designs/npu_blocks/attention_hbm_replay_controller_c4/metrics.csv",
                        "status": "ok",
                    },
                    "metric_summary": {
                        "critical_path_ns": 0.42,
                        "die_area": 12450.0,
                        "total_power_mw": 0.014,
                    },
                },
            ],
            "trial_summary": {
                "metrics": {}
            },
        },
    )

    report = build_report(args)
    score32_row = report["rows"][0]

    assert score32_row["candidate_id"] == "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best"
    assert score32_row["score32_hbm_controller_replay_ppa"] == {
        "critical_path_ns_best": 0.42,
        "die_area_best": 12450.0,
        "total_power_mw_best": 0.014,
        "source": "proposals",
        "artifact_item_id": "l1_decoder_attention_hbm_replay_controller_ppa_v1",
        "metrics_csv": "runs/designs/npu_blocks/attention_hbm_replay_controller_c4/metrics.csv",
    }
    assert "HBM replay controller control timing is backed by measured Nangate45 RTL PPA." in score32_row[
        "remaining_abstractions"
    ]
    assert "controller replay is deterministic cycle-level but not RTL-timing accurate" not in score32_row[
        "remaining_abstractions"
    ]
    assert report["inputs"]["score32_hbm_controller_replay_ppa_json"] == str(args.score32_hbm_controller_replay_ppa_json)
    assert report["inputs"]["score32_hbm_controller_replay_ppa_metrics"] == {
        "critical_path_ns_best": 0.42,
        "die_area_best": 12450.0,
        "total_power_mw_best": 0.014,
        "source": "proposals",
        "artifact_item_id": "l1_decoder_attention_hbm_replay_controller_ppa_v1",
        "metrics_csv": "runs/designs/npu_blocks/attention_hbm_replay_controller_c4/metrics.csv",
    }
    assert any(
        "RTL PPA for the replay controller control path." in item for item in report["assumptions"]
    )

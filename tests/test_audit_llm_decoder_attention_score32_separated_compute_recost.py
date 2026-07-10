from argparse import Namespace
import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_score32_separated_compute_recost import build_report


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _inputs(tmp_path: Path) -> Namespace:
    args = Namespace(
        mixed_int8_energy_json=tmp_path / "energy.json",
        score32_measured_command_control_json=tmp_path / "command.json",
        score32_quality_json=tmp_path / "quality.json",
        hbm_controller_ppa_json=tmp_path / "controller.json",
        quality_aware_frontier_json=tmp_path / "frontier.json",
    )
    _write(
        args.mixed_int8_energy_json,
        {
            "best": {
                "latency_us": 1000,
                "precision_profile": "q8_k8_v8_score32",
                "token_throughput_per_s": 1000,
                "compute_area_um2": 1000000,
                "substituted_block_clock_ns": 2,
                "substituted_compute_power_mw_only": 10,
                "substituted_compute_replica_count": 8,
                "substituted_compute_metrics_csv": "dense/metrics.csv",
                "die_area_mm2": 20,
                "energy_components": {
                    "hbm": {"energy_mj": 3},
                    "noc": {"energy_mj": 0.2},
                    "sram": {"energy_mj": 0.1},
                },
            }
        },
    )
    _write(
        args.score32_measured_command_control_json,
        {
            "best_requested": {
                "clock_ns": 5,
                "precision_profile": "q8_k8_v8_score32",
                "die_area_mm2": 20,
                "cluster_count": 4,
                "selected_l1_overhead_area_um2": 200000,
                "measured_l1_overhead_clock_ns": 4,
                "measured_l1_overhead_power_mw": 2,
                "measured_softmax_weight_metrics_csv": "softmax/metrics.csv",
                "measured_command_dispatch_control_area_um2": 10000,
                "measured_command_dispatch_control_clock_ns": 1,
                "measured_command_dispatch_control_power_mw": 0.5,
                "substituted_compute_replica_count": 7,
                "substituted_block_area_um2": 900000,
                "substituted_block_power_mw": 30,
            }
        },
    )
    _write(
        args.score32_quality_json,
        {
            "decision": {"status": "mixed_int8_generation_quality_pass"},
            "best_candidate": {
                "candidate_id": "score32_exp_lut_div",
                "free_running_match_rate": 0.9,
                "teacher_forced_nll_delta_mean": 0.01,
            },
        },
    )
    _write(
        args.hbm_controller_ppa_json,
        {
            "item_id": "controller_ppa",
            "proposals": [
                {
                    "metrics_ref": {"status": "ok", "metrics_csv": "controller_c4/metrics.csv"},
                    "metric_summary": {"critical_path_ns": 3, "die_area": 50000, "total_power_mw": 1},
                }
            ],
        },
    )
    _write(
        args.quality_aware_frontier_json,
        {
            "rows": [
                {
                    "family": "score32_exp_lut_div",
                    "candidate_id": "old_score32",
                    "token_throughput_per_s": 100,
                    "energy_mj_per_token": 10,
                    "compute_area_mm2": 5,
                },
                {
                    "family": "measured_exact_fp16_gqa8_kv8",
                    "candidate_id": "fp16",
                    "token_throughput_per_s": 50,
                    "energy_mj_per_token": 2,
                    "compute_area_mm2": 8,
                },
            ]
        },
    )
    return args


def test_separated_recost_uses_measured_components_and_remains_nonpromotable(tmp_path: Path) -> None:
    report = build_report(_inputs(tmp_path))
    candidate = report["candidate"]

    assert report["decision"] == "score32_separated_compute_measured_component_frontier_requires_rtl"
    assert candidate["logic_area_mm2"] == 1.26
    assert candidate["active_power_mw"] == 13.5
    assert candidate["compute_control_energy_mj_per_token"] == 0.0135
    assert candidate["energy_mj_per_token"] == 3.3135
    assert candidate["token_throughput_per_s"] == 1000
    assert candidate["timing_ok"] is True
    assert candidate["quality_backed"] is True
    assert candidate["quality_target_backed"] is True
    assert candidate["precision_aligned"] is True
    assert candidate["promotable"] is False
    assert report["comparisons"]["vs_current_score32"] == {
        "candidate_id": "old_score32",
        "throughput_ratio": 10.0,
        "energy_ratio": 0.33135,
        "logic_area_ratio": 0.252,
    }


def test_separated_recost_records_component_clock_miss(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.score32_measured_command_control_json.read_text(encoding="utf-8"))
    payload["best_requested"]["measured_l1_overhead_clock_ns"] = 6
    _write(args.score32_measured_command_control_json, payload)

    report = build_report(args)

    assert report["decision"] == "score32_separated_compute_recost_not_ready"
    assert report["candidate"]["timing_ok"] is False
    assert report["candidate"]["components"][1]["clock_ok"] is False


def test_separated_recost_does_not_join_quality_across_precision_profiles(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.mixed_int8_energy_json.read_text(encoding="utf-8"))
    payload["best"]["precision_profile"] = "q8_k8_v6_recip_lut"
    _write(args.mixed_int8_energy_json, payload)

    report = build_report(args)
    candidate = report["candidate"]

    assert report["decision"] == "score32_separated_compute_recost_requires_precision_aligned_rtl"
    assert candidate["quality_target_backed"] is True
    assert candidate["quality_backed"] is False
    assert candidate["precision_aligned"] is False
    assert candidate["energy_source_precision_profile"] == "q8_k8_v6_recip_lut"


def test_separated_recost_rejects_missing_energy_component(tmp_path: Path) -> None:
    args = _inputs(tmp_path)
    payload = json.loads(args.mixed_int8_energy_json.read_text(encoding="utf-8"))
    del payload["best"]["energy_components"]["noc"]
    _write(args.mixed_int8_energy_json, payload)

    try:
        build_report(args)
    except ValueError as exc:
        assert "mixed-int8 noc energy" in str(exc)
    else:
        raise AssertionError("missing NoC energy must fail closed")

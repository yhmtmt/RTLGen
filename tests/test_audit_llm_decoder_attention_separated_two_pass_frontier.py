from argparse import Namespace
import csv
import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_separated_two_pass_frontier import build_report


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_metrics_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status", "critical_path_ns", "instance_area_um2"])
        writer.writeheader()
        writer.writerow({"status": "ok", "critical_path_ns": "7.5", "instance_area_um2": "100000"})


def _separated_source_json(path: Path) -> Path:
    return _write_json(
        path,
        {
            "candidate": {
                "candidate_id": "score32_separated_dense_int8_shared_vector_softmax_c16_hbm_c4",
                "precision_profile": "q8_k8_v8_score32",
                "latency_us": 1000.0,
                "compute_control_energy_mj_per_token": 0.0135,
                "hbm_energy_mj_per_token": 2.0,
                "noc_energy_mj_per_token": 0.2,
                "sram_energy_mj_per_token": 0.1,
                "logic_area_mm2": 5.0,
                "die_area_mm2": 20.0,
                "active_power_mw": 13.5,
                "schedule_clock_ns": 5.0,
                "timing_ok": True,
                "remaining_abstractions": [
                    "the inherited row was not precision-aligned with the score32 zero-tail target",
                    "producer-to-consumer ready/valid composition remains abstract",
                ],
                "components": [
                    {
                        "component": "dense_int8_gemm_fabric",
                        "area_um2": 4_000_000.0,
                        "power_mw": 10.0,
                        "critical_path_ns": 2.0,
                        "clock_ok": True,
                        "source": "dense/metrics.csv",
                    },
                    {
                        "component": "shared_score32_vector_softmax_overhead",
                        "area_um2": 200_000.0,
                        "power_mw": 2.0,
                        "critical_path_ns": 4.0,
                        "clock_ok": True,
                        "source": "softmax/metrics.csv",
                    },
                    {
                        "component": "command_dispatch_control",
                        "area_um2": 100_000.0,
                        "power_mw": 1.0,
                        "critical_path_ns": 1.0,
                        "clock_ok": True,
                        "source": "dispatch/metrics.csv",
                    },
                    {
                        "component": "hbm_replay_controller_c4",
                        "area_um2": 700_000.0,
                        "power_mw": 0.5,
                        "critical_path_ns": 3.0,
                        "clock_ok": True,
                        "source": "controller/metrics.csv",
                    },
                ],
            }
        },
    )


def _quality_json(path: Path) -> Path:
    return _write_json(
        path,
        {
            "decision": {"status": "mixed_int8_generation_quality_pass"},
            "best_candidate": {
                "candidate_id": "score32_zero_tail_two_pass",
                "free_running_match_rate": 0.91,
                "teacher_forced_nll_delta_mean": 0.005,
            },
        },
    )


def _iterdiv_json(path: Path, metrics_csv: str) -> Path:
    return _write_json(
        path,
        {
            "proposals": [
                {
                    "metrics_ref": {"status": "ok", "metrics_csv": metrics_csv},
                    "metric_summary": {
                        "critical_path_ns": 7.5,
                        "die_area": 999999.0,
                        "total_power_mw": 2.0,
                    },
                }
            ]
        },
    )


def _build_args(tmp_path: Path, frontier_input: Path) -> Namespace:
    return Namespace(
        separated_compute_recost_json=tmp_path / "source.json",
        score_sram_recost_json=frontier_input,
        zero_tail_quality_json=tmp_path / "quality.json",
        iterdiv_ppa_json=tmp_path / "iterdiv.json",
        head_count=32,
        divide_cycles_per_head=480,
        clock_ns=10.0,
    )


def test_separated_two_pass_frontier_recosts_from_score_sram_ratio(tmp_path: Path) -> None:
    _separated_source_json(tmp_path / "source.json")
    _quality_json(tmp_path / "quality.json")
    _write_metrics_csv(tmp_path / "iterdiv" / "metrics.csv")
    _iterdiv_json(tmp_path / "iterdiv.json", "iterdiv/metrics.csv")
    frontier_input = _write_json(
        tmp_path / "score_sram.json",
        {
            "diagnosis": {
                "score_buffer_energy_mj_per_token": 0.25,
                "score_buffer_area_mm2": 8.0,
            },
            "rows": [
                {
                    "placement_efficiency": 0.75,
                    "source_score32_latency_us": 5000.0,
                    "projected_latency_us_hbm_share_scaled": 5500.0,
                    "score_buffer_envelope_area_um2": 10_000_000.0,
                    "shared_sram_capacity_mib": 30.0,
                    "hbm_byte_share": 0.90,
                    "hbm_share_scale_vs_measured_sram": 1.1,
                },
                {
                    "placement_efficiency": 0.55,
                    "source_score32_latency_us": 5000.0,
                    "projected_latency_us_hbm_share_scaled": 5750.0,
                    "score_buffer_envelope_area_um2": 14_000_000.0,
                    "shared_sram_capacity_mib": 16.0,
                    "hbm_byte_share": 0.95,
                    "hbm_share_scale_vs_measured_sram": 1.15,
                },
            ],
        },
    )

    report = build_report(_build_args(tmp_path, frontier_input))

    assert report["decision"] == "score32_separated_two_pass_frontier_ranked"
    assert report["iterdiv_metrics"]["area_metric"] == "instance_area_um2"
    assert report["schedule"]["per_head_divider_latency_us"] == 4.8
    assert report["schedule"]["shared_divider_latency_us"] == 153.6

    nominal_per_head = report["latency_rank"][0]
    nominal_shared = next(
        row
        for row in report["rows"]
        if row["placement_scenario"] == "nominal" and row["divider_deployment"] == "shared"
    )
    conservative_shared = next(
        row
        for row in report["rows"]
        if row["placement_scenario"] == "conservative" and row["divider_deployment"] == "shared"
    )

    assert nominal_per_head["candidate_id"] == "score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv"
    assert nominal_per_head["latency_us"] == 1104.8
    assert nominal_shared["latency_us"] == 1253.6
    assert conservative_shared["latency_us"] == 1303.6
    assert nominal_per_head["hbm_share_scaled_latency_us"] == 1100.0
    assert nominal_per_head["hbm_energy_mj_per_token"] == 2.2
    assert nominal_per_head["energy_mj_per_token"] == 2.7618072
    assert conservative_shared["energy_mj_per_token"] == 2.8618072
    assert nominal_per_head["compute_control_service_energy_mj_per_token"] == 0.0118072
    assert nominal_per_head["removed_shared_score32_energy_mj_per_token"] == 0.002
    assert nominal_per_head["divider_energy_mj_per_token"] == nominal_shared["divider_energy_mj_per_token"] == 0.0003072
    assert nominal_per_head["logic_plus_service_area_mm2"] == 8.0
    assert nominal_shared["logic_plus_service_area_mm2"] == 4.9
    assert nominal_per_head["score_sram_macro_area_mm2"] == 8.0
    assert nominal_per_head["score_sram_envelope_area_mm2"] == 10.0
    assert nominal_per_head["embodied_logic_plus_score_macro_area_mm2"] == 16.0
    assert nominal_shared["embodied_logic_plus_score_macro_area_mm2"] == 12.9
    assert nominal_per_head["active_power_mw"] == 75.5
    assert nominal_shared["active_power_mw"] == 13.5
    assert nominal_per_head["precision_aligned"] is True
    assert nominal_per_head["quality_backed"] is True
    assert "precision-aligned" not in " ".join(nominal_per_head["remaining_abstractions"]).lower()
    assert report["diagnosis"]["shared_divider_latency_penalty_us"] == 148.8
    assert report["diagnosis"]["per_head_divider_area_premium_mm2"] == 3.1
    assert report["diagnosis"]["recommended_total_energy_mj_per_token"] == 2.7618072
    assert report["diagnosis"]["recommended_embodied_area_mm2"] == 16.0
    assert report["diagnosis"]["precision_status"] == "mixed_int8_generation_quality_pass"
    assert report["diagnosis"]["precision_aligned"] is True


def test_separated_two_pass_frontier_accepts_integrated_frontier_rows(tmp_path: Path) -> None:
    _separated_source_json(tmp_path / "source.json")
    _quality_json(tmp_path / "quality.json")
    _write_metrics_csv(tmp_path / "iterdiv" / "metrics.csv")
    _iterdiv_json(tmp_path / "iterdiv.json", "iterdiv/metrics.csv")
    frontier_input = _write_json(
        tmp_path / "integrated_frontier.json",
        {
            "rows": [
                {
                    "candidate_id": "score32_zero_tail_two_pass_nominal_per_head_iterdiv",
                    "placement_scenario": "nominal",
                    "placement_efficiency": 0.75,
                    "divider_deployment": "per_head",
                    "score_sram_source_latency_us": 5000.0,
                    "score_sram_latency_delta_us": 500.0,
                    "score_sram_energy_mj_per_token": 0.25,
                    "score_sram_macro_area_mm2": 8.0,
                    "score_sram_envelope_area_mm2": 10.0,
                    "shared_sram_capacity_mib": 30.0,
                    "hbm_byte_share": 0.90,
                },
                {
                    "candidate_id": "score32_zero_tail_two_pass_nominal_shared_iterdiv",
                    "placement_scenario": "nominal",
                    "placement_efficiency": 0.75,
                    "divider_deployment": "shared",
                    "score_sram_source_latency_us": 5000.0,
                    "score_sram_latency_delta_us": 500.0,
                    "score_sram_energy_mj_per_token": 0.25,
                    "score_sram_macro_area_mm2": 8.0,
                    "score_sram_envelope_area_mm2": 10.0,
                    "shared_sram_capacity_mib": 30.0,
                    "hbm_byte_share": 0.90,
                },
                {
                    "candidate_id": "score32_zero_tail_two_pass_conservative_per_head_iterdiv",
                    "placement_scenario": "conservative",
                    "placement_efficiency": 0.55,
                    "divider_deployment": "per_head",
                    "score_sram_source_latency_us": 5000.0,
                    "score_sram_latency_delta_us": 750.0,
                    "score_sram_energy_mj_per_token": 0.25,
                    "score_sram_macro_area_mm2": 8.0,
                    "score_sram_envelope_area_mm2": 14.0,
                    "shared_sram_capacity_mib": 16.0,
                    "hbm_byte_share": 0.95,
                },
                {
                    "candidate_id": "score32_zero_tail_two_pass_conservative_shared_iterdiv",
                    "placement_scenario": "conservative",
                    "placement_efficiency": 0.55,
                    "divider_deployment": "shared",
                    "score_sram_source_latency_us": 5000.0,
                    "score_sram_latency_delta_us": 750.0,
                    "score_sram_energy_mj_per_token": 0.25,
                    "score_sram_macro_area_mm2": 8.0,
                    "score_sram_envelope_area_mm2": 14.0,
                    "shared_sram_capacity_mib": 16.0,
                    "hbm_byte_share": 0.95,
                },
            ]
        },
    )

    report = build_report(_build_args(tmp_path, frontier_input))

    assert report["rows"][0]["family"] == "score32_separated_zero_tail_two_pass_iterdiv"
    assert report["diagnosis"]["recommended_candidate"] == "score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv"
    assert report["rows"][0]["inherited_schedule_abstraction"]["hbm_share_scale"] == 1.1
    assert report["rows"][0]["inherited_hbm_service_abstraction"]["scaled_hbm_energy_mj_per_token"] == 2.2
    assert report["inputs"]["separated_compute_recost_json"] == str(tmp_path / "source.json")
    assert report["inputs"]["score_sram_recost_json"] == str(frontier_input)

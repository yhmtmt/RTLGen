from argparse import Namespace
import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_two_pass_integrated_frontier_ranking import build_report


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_two_pass_recost_exposes_shared_and_per_head_tradeoff(tmp_path: Path) -> None:
    source = _write(
        tmp_path / "source.json",
        {
            "rows": [
                {
                    "candidate_id": "score32_old",
                    "latency_us": 1000.0,
                    "energy_mj_per_token": 10.0,
                    "compute_area_mm2": 20.0,
                    "die_area_mm2": 100.0,
                }
            ]
        },
    )
    sram = _write(
        tmp_path / "sram.json",
        {
            "diagnosis": {
                "score_buffer_energy_mj_per_token": 0.25,
                "score_buffer_area_mm2": 8.0,
            },
            "rows": [
                {
                    "placement_efficiency": efficiency,
                    "source_score32_latency_us": 1000.0,
                    "projected_latency_us_hbm_share_scaled": latency,
                    "score_buffer_envelope_area_um2": envelope,
                    "shared_sram_capacity_mib": capacity,
                    "hbm_byte_share": share,
                }
                for efficiency, latency, envelope, capacity, share in (
                    (0.75, 1010.0, 10_000_000, 30.0, 0.99),
                    (0.55, 1020.0, 14_000_000, 16.0, 0.995),
                )
            ],
        },
    )
    quality = _write(
        tmp_path / "quality.json",
        {
            "decision": {"status": "mixed_int8_generation_quality_pass"},
            "best_candidate": {"free_running_match_rate": 0.875, "teacher_forced_nll_delta_mean": 0.01},
        },
    )
    ppa = _write(
        tmp_path / "ppa.json",
        {
            "proposals": [
                {
                    "metrics_ref": {"status": "ok", "metrics_csv": "iterdiv/metrics.csv"},
                    "metric_summary": {"critical_path_ns": 7.5, "die_area": 100_000, "total_power_mw": 2.0},
                }
            ]
        },
    )

    report = build_report(
        Namespace(
            source_frontier_ranking_json=source,
            score_sram_recost_json=sram,
            zero_tail_quality_json=quality,
            iterdiv_ppa_json=ppa,
            head_count=32,
            divide_cycles_per_head=480,
            clock_ns=10.0,
        )
    )

    per_head = report["latency_rank"][0]
    shared = next(row for row in report["rows"] if row["placement_scenario"] == "nominal" and row["divider_deployment"] == "shared")
    assert per_head["latency_us"] == 1014.8
    assert shared["latency_us"] == 1163.6
    assert per_head["score_sram_latency_delta_us"] == 10.0
    assert per_head["divider_instances"] == 32
    assert shared["divider_instances"] == 1
    assert per_head["divider_energy_mj_per_token"] == shared["divider_energy_mj_per_token"]
    assert per_head["compute_plus_service_logic_area_mm2"] == 23.2
    assert shared["compute_plus_service_logic_area_mm2"] == 20.1
    assert per_head["quality_backed"] is True
    assert report["diagnosis"]["shared_divider_latency_penalty_us"] == 148.8

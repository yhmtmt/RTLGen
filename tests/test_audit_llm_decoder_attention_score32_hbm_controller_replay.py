from argparse import Namespace
import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_score32_hbm_controller_replay import (
    _simulate_replay_cycles,
    build_report,
)


def test_row_misses_increase_replay_cycles() -> None:
    channels = [0, 1, 0, 1]
    miss_flags_no = [False, False, False, False]
    miss_flags_yes = [True, True, True, True]

    without_miss = _simulate_replay_cycles(
        channel_count=2,
        channel_bandwidth_bytes_per_cycle=256,
        burst_bytes=128,
        channels=channels,
        miss_flags=miss_flags_no,
        request_overhead_cycles=2,
        row_miss_penalty_cycles=16,
        scheduler_gap_cycles=0,
        outstanding=4,
        scheduler_efficiency=0.9,
    )
    with_miss = _simulate_replay_cycles(
        channel_count=2,
        channel_bandwidth_bytes_per_cycle=256,
        burst_bytes=128,
        channels=channels,
        miss_flags=miss_flags_yes,
        request_overhead_cycles=2,
        row_miss_penalty_cycles=16,
        scheduler_gap_cycles=0,
        outstanding=4,
        scheduler_efficiency=0.9,
    )

    assert with_miss > without_miss


def test_larger_outstanding_does_not_worsen_replay_cycles() -> None:
    channels = [0, 1, 0, 1, 0, 1, 0, 1]
    miss_flags = [True, False, False, True, False, False, False, True]

    tight = _simulate_replay_cycles(
        channel_count=2,
        channel_bandwidth_bytes_per_cycle=64,
        burst_bytes=256,
        channels=channels,
        miss_flags=miss_flags,
        request_overhead_cycles=4,
        row_miss_penalty_cycles=12,
        scheduler_gap_cycles=1,
        outstanding=1,
        scheduler_efficiency=0.85,
    )
    roomy = _simulate_replay_cycles(
        channel_count=2,
        channel_bandwidth_bytes_per_cycle=64,
        burst_bytes=256,
        channels=channels,
        miss_flags=miss_flags,
        request_overhead_cycles=4,
        row_miss_penalty_cycles=12,
        scheduler_gap_cycles=1,
        outstanding=4,
        scheduler_efficiency=0.85,
    )

    assert roomy <= tight


def test_build_report_includes_best_latency_and_diagnosis(tmp_path: Path) -> None:
    score32_hbm = tmp_path / "score32_hbm.json"
    score32_physical = tmp_path / "score32_physical.json"
    score32_hbm.write_text(
        json.dumps(
            {
                "best_latency": {
                    "latency_us": 12.5,
                    "source_latency_us": 12.5,
                    "hbm_energy_mj_per_token": 0.5,
                    "compute_power_mw": 200.0,
                }
            }
        ),
        encoding="utf-8",
    )
    score32_physical.write_text(
        json.dumps(
            {
                "best_requested": {
                    "onchip_full_tile_bytes": 1048576,
                    "hbm_byte_share": 1.0,
                    "replica_recost_latency_us": 12.5,
                    "tile_hbm_cycles": 100,
                    "replica_recost_tile_service_cycles": 90,
                    "tile_waves": 1,
                    "layers": 32,
                    "clock_ns": 1.0,
                    "replica_recost_compute_power_mw": 150.0,
                }
            }
        ),
        encoding="utf-8",
    )

    args = Namespace(
        score32_hbm_dram_service_json=score32_hbm,
        score32_physical_feasibility_json=score32_physical,
        channel_count_list=[1],
        channel_bandwidth_bytes_per_cycle_list=[128],
        burst_bytes_list=[256],
        row_span_bursts_list=[1],
        row_hit_rate_list=[1.0],
        request_overhead_cycles_list=[2],
        row_miss_penalty_cycles_list=[8],
        hbm_outstanding_list=[4],
        scheduler_gap_cycles_list=[0],
        scheduler_efficiency_list=[1.0],
        top_k=5,
    )

    report = build_report(args)
    assert "best_latency" in report
    assert "diagnosis" in report
    assert "best_latency_us" in report["diagnosis"]
    assert "best_latency_total_energy_mj_per_token" in report["diagnosis"]
    assert isinstance(report["top_rows"], list)
    assert len(report["top_rows"]) == 1

from npu.eval.estimate_llm_decoder_producer_ranker_service_compatibility import build_report


def test_service_compatibility_selects_low_power_serial_when_it_keeps_up() -> None:
    producer_service = {
        "model": "producer_service_test",
        "inputs": {"clock_ns": 1.0},
        "producer_service_sweep": [
            {
                "scenario": "shared_gemm_stage_serial",
                "vocab_size": 256,
                "hidden_size": 64,
                "producer_lanes": 64,
                "tile_count": 4,
                "macs_per_cycle": 4096,
                "memory_bandwidth_bytes_per_cycle": 128.0,
                "producer_ii_cycles": 80,
                "producer_latency_cycles": 16,
                "producer_latency_us_per_token": 0.256,
                "service_limiter": "weight_memory",
            }
        ],
    }
    serial_ranker = {
        "model": "serial_ranker_test",
        "variants": [
            {
                "status": "ok",
                "top": "serial_lpc1",
                "lanes_per_cycle": 1,
                "tile_scan_cycles": 64,
                "ii_goal_cycles": 65,
                "metrics_row": {
                    "critical_path_ns": "2.8",
                    "die_area": "810000",
                    "total_power_mw": "0.006",
                    "stage_elapsed_seconds": "1.0",
                },
                "synthesis": {"log_tail": ["[INFO GPL-1002] Placed Cell Area 19000.0"]},
            }
        ],
    }
    rank_tree = {
        "model": "rank_tree_test",
        "variants": [
            {
                "status": "ok",
                "top": "ranktree_radix2",
                "radix": 2,
                "pipeline_stages": 6,
                "metrics_row": {
                    "critical_path_ns": "3.0",
                    "die_area": "810000",
                    "total_power_mw": "0.015",
                },
                "synthesis": {"log_tail": ["[INFO GPL-1002] Placed Cell Area 34000.0"]},
            }
        ],
    }

    report = build_report(
        producer_service=producer_service,
        serial_ranker=serial_ranker,
        rank_tree=rank_tree,
    )

    assert report["recommendation"]["decision"] == "serial_ranker_service_compatible"
    best = report["recommendation"]["lowest_power_feasible"]
    assert best["ranker"] == "serial_lpc1"
    assert best["throughput_margin_cycles"] == 15
    assert best["ranker_placed_cell_area_um2"] == 19000.0


def test_single_ranker_for_wider_producer_scales_service_cycles() -> None:
    producer_service = {
        "model": "producer_service_test",
        "inputs": {"clock_ns": 1.0},
        "producer_service_sweep": [
            {
                "scenario": "shared_gemm_stage_serial",
                "vocab_size": 512,
                "hidden_size": 64,
                "producer_lanes": 128,
                "tile_count": 4,
                "macs_per_cycle": 4096,
                "memory_bandwidth_bytes_per_cycle": 128.0,
                "producer_ii_cycles": 100,
                "producer_latency_cycles": 16,
                "producer_latency_us_per_token": 0.256,
                "service_limiter": "compute_array",
            }
        ],
    }
    serial_ranker = {
        "model": "serial_ranker_test",
        "variants": [
            {
                "status": "ok",
                "top": "serial_lpc1",
                "lanes_per_cycle": 1,
                "tile_scan_cycles": 64,
                "ii_goal_cycles": 65,
                "metrics_row": {"total_power_mw": "0.006"},
            }
        ],
    }
    rank_tree = {"model": "rank_tree_test", "variants": []}

    report = build_report(
        producer_service=producer_service,
        serial_ranker=serial_ranker,
        rank_tree=rank_tree,
    )

    rows = {
        row["integration"]: row
        for row in report["compatibility_sweep"]
        if row["ranker"] == "serial_lpc1"
    }
    assert rows["single_r64_ranker"]["ranker_service_cycles_per_producer_tile"] == 130
    assert rows["single_r64_ranker"]["throughput_ok"] is False
    assert rows["banked_r64_rankers"]["ranker_service_cycles_per_producer_tile"] == 65
    assert rows["banked_r64_rankers"]["throughput_ok"] is True

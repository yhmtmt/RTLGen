from npu.eval.estimate_llm_decoder_output_projection_producer_memory_hierarchy import build_report


def _frontier() -> dict:
    return {
        "model": "frontier",
        "focus_summary": [
            {
                "label": "toy",
                "sequence_length": 128,
                "hidden_size": 64,
                "vocab_size": 256,
                "dominant_component": "output_projection_producer_ranker",
            }
        ],
    }


def _calibration() -> dict:
    return {
        "model": "calibration",
        "calibrated_coupled_ranker_sweep": [
            {
                "status": "ok",
                "hidden_size": 64,
                "vocab_size": 256,
                "producer_lanes": 64,
                "macs_per_cycle": 4096,
                "producer_ii_cycles": 64,
                "producer_latency_us_per_token": 0.2,
                "calibrated_coupled_latency_us_per_token": 0.2,
                "calibrated_ranker_latency_us_per_token": 0.01,
            }
        ],
    }


def test_memory_hierarchy_limits_cache_hit_by_capacity() -> None:
    report = build_report(
        frontier=_frontier(),
        calibration=_calibration(),
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        offchip_bw_bytes_per_cycle_list=[128.0],
        local_cache_bw_bytes_per_cycle_list=[1024.0],
        cache_capacity_mb_list=[0.0],
        cache_hit_rate_list=[1.0],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    row = report["memory_hierarchy_sweep"][0]
    assert row["effective_cache_hit_rate"] == 0.0
    assert row["offchip_weight_cycles_per_tile"] == 64
    assert row["producer_latency_us_parallel"] == 0.194
    assert report["shape_summaries"][0]["baseline_producer_us"] == 0.2


def test_memory_hierarchy_resident_weights_reduce_latency() -> None:
    report = build_report(
        frontier=_frontier(),
        calibration=_calibration(),
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        offchip_bw_bytes_per_cycle_list=[128.0],
        local_cache_bw_bytes_per_cycle_list=[8192.0],
        cache_capacity_mb_list=[1.0],
        cache_hit_rate_list=[1.0],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    summary = report["shape_summaries"][0]
    best = summary["best_parallel"]
    assert best["effective_cache_hit_rate"] == 1.0
    assert best["parallel_limiter"] == "compute_array"
    assert best["producer_latency_us_parallel"] < summary["baseline_producer_us"]
    assert summary["best_parallel_speedup_vs_baseline"] > 1.0

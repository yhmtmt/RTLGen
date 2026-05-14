from npu.eval.estimate_llm_decoder_resident_weight_ranker_fallback import build_report


def _cadence_row(*, producer_ii: int, producer_lanes: int = 64, tile_count: int = 32) -> dict:
    return {
        "vocab_size": 50257,
        "hidden_size": 768,
        "producer_lanes": producer_lanes,
        "tile_count": tile_count,
        "macs_per_cycle": 32768,
        "memory_bandwidth_bytes_per_cycle": 256,
        "weight_cache_hit_rate": 1.0,
        "producer_ii_cycles": producer_ii,
        "service_limiter": "compute",
        "selected_ranker": {"decision": "serial_ranker_not_safe_at_this_cadence"},
    }


def _rank_tree() -> dict:
    return {
        "variants": [
            {
                "status": "ok",
                "radix": 4,
                "pipeline_stages": 3,
                "metrics_row": {
                    "critical_path_ns": "2.9",
                    "die_area": "800000",
                    "total_power_mw": "0.02",
                },
                "synthesis": {"log_tail": ["Placed Cell Area 32000.0"]},
            }
        ]
    }


def _cadence(*rows: dict) -> dict:
    return {
        "ranker_zero_backpressure_thresholds": {
            "serial_lpc1": {"min_zero_backpressure_ii_cycles": 384},
            "serial_lpc2": {"min_zero_backpressure_ii_cycles": 65},
            "serial_lpc4": {"min_zero_backpressure_ii_cycles": 33},
        },
        "ranker_costs": {
            "serial_lpc1": {"ranker_service_cycles": 65, "total_power_mw": 0.006},
            "serial_lpc2": {"ranker_service_cycles": 33, "total_power_mw": 0.008},
            "serial_lpc4": {"ranker_service_cycles": 17, "total_power_mw": 0.011},
        },
        "cadence_sweep": list(rows),
    }


def test_resident_fast_row_prefers_no_buffer_rank_tree() -> None:
    report = build_report(
        cadence_sensitivity=_cadence(_cadence_row(producer_ii=2, tile_count=64)),
        rank_tree=_rank_tree(),
        logit_bits=16,
        small_buffer_tiles=32,
    )

    selected = report["fallback_rows"][0]["recommended"]
    assert selected["strategy"] == "single_r64_ranktrees_ranktree_radix4"
    assert selected["required_buffer_r64_tiles"] == 0
    assert report["recommendation"]["decision"] == "rank_tree_fallback_preferred_for_resident_weight"


def test_near_threshold_row_prefers_small_buffered_serial_lpc4() -> None:
    report = build_report(
        cadence_sensitivity=_cadence(_cadence_row(producer_ii=32, tile_count=64)),
        rank_tree=_rank_tree(),
        logit_bits=16,
        small_buffer_tiles=32,
    )

    selected = report["fallback_rows"][0]["recommended"]
    assert selected["strategy"] == "buffered_serial_lpc4"
    assert 0 < selected["required_buffer_r64_tiles"] <= 32
    assert selected["required_buffer_bytes"] == selected["required_buffer_r64_tiles"] * 128


def test_wide_fast_row_can_use_banked_rank_tree_without_buffer() -> None:
    report = build_report(
        cadence_sensitivity=_cadence(_cadence_row(producer_ii=1, producer_lanes=128, tile_count=64)),
        rank_tree=_rank_tree(),
        logit_bits=16,
        small_buffer_tiles=32,
    )

    selected = report["fallback_rows"][0]["recommended"]
    assert selected["strategy"] == "banked_r64_ranktrees_ranktree_radix4"
    assert selected["ranker_instances"] == 2
    assert selected["required_buffer_r64_tiles"] == 0

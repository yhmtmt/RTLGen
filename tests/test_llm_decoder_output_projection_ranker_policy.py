from npu.eval.promote_llm_decoder_output_projection_ranker_policy import build_report


def _cadence_row(*, lanes: int, ii: int, hit: float) -> dict:
    return {
        "vocab_size": 50257,
        "hidden_size": 768,
        "producer_lanes": lanes,
        "tile_count": 786,
        "macs_per_cycle": 8192,
        "memory_bandwidth_bytes_per_cycle": 64,
        "weight_cache_hit_rate": hit,
        "producer_ii_cycles": ii,
        "service_limiter": "weight_memory" if hit < 1.0 else "compute_array",
    }


def _serial_wrapper() -> dict:
    return {
        "decision": {"decision": "serial_lpc1_producer_coupled_wrapper_promoted"},
        "target": {"producer_ii_cycles": 384},
        "selected_metrics": {"total_power_mw": 0.0065},
    }


def _ranktree_promotion() -> dict:
    return {
        "decision": {"decision": "resident_weight_ranktree_fallback_promoted"},
        "selected_metrics": {"total_power_mw": 0.0114},
        "producer_modes": [
            {"mode": "single_r64_ranktree", "consumer_ii_cycles": 1, "ranker_instances": 1},
            {"mode": "banked_r64_ranktrees", "consumer_ii_cycles": 1, "ranker_instances": 2},
        ],
    }


def test_policy_routes_streaming_to_serial_and_fast_rows_to_ranktree() -> None:
    report = build_report(
        serial_wrapper=_serial_wrapper(),
        cadence_sensitivity={
            "ranker_zero_backpressure_thresholds": {
                "serial_lpc1": {"min_zero_backpressure_ii_cycles": 384}
            },
            "cadence_sweep": [
                _cadence_row(lanes=64, ii=384, hit=0.0),
                _cadence_row(lanes=64, ii=154, hit=0.9),
                _cadence_row(lanes=128, ii=8, hit=1.0),
            ],
        },
        ranktree_promotion=_ranktree_promotion(),
    )

    assert report["decision"]["decision"] == "output_projection_ranker_policy_promoted"
    assert report["path_summary"]["path_counts"] == {
        "serial_lpc1": 1,
        "single_r64_ranktree": 1,
        "banked_r64_ranktrees": 1,
    }
    assert report["policy_rows"][0]["selected_path"] == "serial_lpc1"
    assert report["policy_rows"][1]["selected_path"] == "single_r64_ranktree"
    assert report["policy_rows"][2]["selected_path"] == "banked_r64_ranktrees"
    assert all(check["passed"] for check in report["checks"])


def test_policy_blocks_when_banked_ranktree_mode_missing() -> None:
    ranktree = _ranktree_promotion()
    ranktree["producer_modes"] = [ranktree["producer_modes"][0]]
    report = build_report(
        serial_wrapper=_serial_wrapper(),
        cadence_sensitivity={
            "ranker_zero_backpressure_thresholds": {
                "serial_lpc1": {"min_zero_backpressure_ii_cycles": 384}
            },
            "cadence_sweep": [_cadence_row(lanes=128, ii=8, hit=1.0)],
        },
        ranktree_promotion=ranktree,
    )

    assert report["decision"]["decision"] == "output_projection_ranker_policy_blocked"
    assert report["path_summary"]["uncovered_rows"] == 1
    assert report["policy_rows"][0]["coverage_status"] == "uncovered_ranktree_mode"


def test_policy_blocks_when_serial_wrapper_not_promoted() -> None:
    serial = _serial_wrapper()
    serial["decision"] = {"decision": "serial_lpc1_producer_coupled_wrapper_blocked"}
    report = build_report(
        serial_wrapper=serial,
        cadence_sensitivity={"cadence_sweep": [_cadence_row(lanes=64, ii=384, hit=0.0)]},
        ranktree_promotion=_ranktree_promotion(),
    )

    assert report["decision"]["decision"] == "output_projection_ranker_policy_blocked"
    assert report["checks"][0]["name"] == "serial_lpc1_wrapper_promoted"
    assert report["checks"][0]["passed"] is False

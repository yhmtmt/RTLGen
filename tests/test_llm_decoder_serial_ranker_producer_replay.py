from npu.eval.probe_llm_decoder_serial_ranker_producer_replay import (
    _make_tile_values,
    _reference_top1,
    build_report,
)


def test_reference_top1_uses_lower_token_tie_break() -> None:
    tiles = _make_tile_values(num_tiles=3, producer_lanes=64)

    assert _reference_top1(tiles, producer_lanes=64) == {"token": 5, "logit": 500}


def test_replay_report_passes_when_all_rtl_rows_match_reference() -> None:
    report = build_report(
        serial_ranker={"model": "decoder_serial_ranker_architecture_v1"},
        service_compatibility={
            "model": "decoder_producer_ranker_service_compatibility_v1",
            "recommendation": {"lowest_power_feasible": {"ranker": "serial_lpc1"}},
        },
        replay_rows=[
            {
                "lanes_per_cycle": 1,
                "scenario": "ii65",
                "producer_ii_cycles": 65,
                "ranker_service_cycles": 65,
                "expected_throughput_ok": True,
                "rtl_sim": {
                    "status": "ok",
                    "expected": {"token": 5, "logit": 500},
                    "observed": {
                        "token": 5,
                        "logit": 500,
                        "tb_backpressure": 0,
                    },
                },
            },
            {
                "lanes_per_cycle": 1,
                "scenario": "ii16",
                "producer_ii_cycles": 16,
                "ranker_service_cycles": 65,
                "expected_throughput_ok": False,
                "rtl_sim": {
                    "status": "ok",
                    "expected": {"token": 5, "logit": 500},
                    "observed": {
                        "token": 5,
                        "logit": 500,
                        "tb_backpressure": 100,
                    },
                },
            },
        ],
        producer_ii_cycles=[16, 65],
        lanes_per_cycle=[1],
        num_tiles=6,
    )

    assert report["decision"]["decision"] == "producer_cadence_replay_passed"
    assert report["decision"]["throughput_safe_rows"] == 1
    assert report["service_compatibility_lowest_power_feasible"]["ranker"] == "serial_lpc1"

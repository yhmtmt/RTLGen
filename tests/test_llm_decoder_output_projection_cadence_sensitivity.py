from npu.eval.estimate_llm_decoder_output_projection_cadence_sensitivity import build_report


def test_cadence_sensitivity_selects_lpc1_for_streaming_weight_cadence() -> None:
    report = build_report(
        serial_ranker={
            "variants": [
                {
                    "status": "ok",
                    "lanes_per_cycle": 1,
                    "ii_goal_cycles": 65,
                    "metrics_row": {"status": "ok", "total_power_mw": "0.006"},
                },
                {
                    "status": "ok",
                    "lanes_per_cycle": 4,
                    "ii_goal_cycles": 17,
                    "metrics_row": {"status": "ok", "total_power_mw": "0.01"},
                },
            ]
        },
        producer_replay={
            "replay_rows": [
                {
                    "lanes_per_cycle": 1,
                    "producer_ii_cycles": 384,
                    "ranker_service_cycles": 65,
                    "rtl_sim": {"status": "ok", "observed": {"tb_backpressure": 0}},
                },
                {
                    "lanes_per_cycle": 4,
                    "producer_ii_cycles": 33,
                    "ranker_service_cycles": 17,
                    "rtl_sim": {"status": "ok", "observed": {"tb_backpressure": 0}},
                },
            ]
        },
        promoted_wrapper={"decision": {"decision": "serial_lpc1_producer_coupled_wrapper_promoted"}},
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[16.0],
        weight_cache_hit_rate_list=[0.0],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    row = report["cadence_sweep"][0]
    assert row["producer_ii_cycles"] == 512
    assert row["selected_ranker"]["ranker"] == "serial_lpc1"
    assert report["risk_summary"]["serial_unsafe_rows"] == 0


def test_cadence_sensitivity_flags_resident_weight_fast_producer() -> None:
    report = build_report(
        serial_ranker={
            "variants": [
                {
                    "status": "ok",
                    "lanes_per_cycle": 4,
                    "ii_goal_cycles": 17,
                    "metrics_row": {"status": "ok", "total_power_mw": "0.01"},
                }
            ]
        },
        producer_replay={
            "replay_rows": [
                {
                    "lanes_per_cycle": 4,
                    "producer_ii_cycles": 33,
                    "ranker_service_cycles": 17,
                    "rtl_sim": {"status": "ok", "observed": {"tb_backpressure": 0}},
                }
            ]
        },
        promoted_wrapper=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        weight_cache_hit_rate_list=[1.0],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    row = report["cadence_sweep"][0]
    assert row["producer_ii_cycles"] == 1
    assert row["selected_ranker"]["decision"] == "serial_ranker_not_safe_at_this_cadence"
    assert report["recommendation"]["decision"] == "resident_weight_can_outpace_serial_ranker"

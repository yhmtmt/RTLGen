from npu.eval.promote_llm_decoder_serial_lpc1_producer_wrapper import build_report


def test_promote_serial_lpc1_report_passes_with_metrics_and_clean_replay() -> None:
    variant = {
        "status": "ok",
        "top": "decoder_r64_k1_serial_rank_lpc1_wrapper",
        "design_dir": "runs/designs/activations/decoder_r64_k1_serial_rank_lpc1_wrapper",
        "lanes_per_cycle": 1,
        "metrics_row": {
            "status": "ok",
            "critical_path_ns": "2.86",
            "die_area": "810000",
            "total_power_mw": "0.0065",
        },
        "synthesis": {"log_tail": ["[INFO GPL-1002] Placed Cell Area 19304.6840"]},
    }
    focused = {
        "status": "ok",
        "expected": {"token": 5, "logit": 500},
        "observed": {"token": 5, "logit": 500, "tb_backpressure": 0},
    }

    report = build_report(
        serial_ranker={"variants": [variant]},
        service_compatibility={
            "recommendation": {
                "lowest_power_feasible": {
                    "ranker": "serial_lpc1",
                    "producer_ii_cycles": 384,
                }
            }
        },
        producer_replay={
            "replay_rows": [
                {
                    "lanes_per_cycle": 1,
                    "producer_ii_cycles": 384,
                    "rtl_sim": focused,
                }
            ]
        },
        focused_rtl_sim=focused,
        lanes_per_cycle=1,
        producer_ii_cycles=384,
    )

    assert report["decision"]["decision"] == "serial_lpc1_producer_coupled_wrapper_promoted"
    assert report["selected_metrics"]["placed_cell_area_um2"] == 19304.684
    assert all(check["passed"] for check in report["checks"])


def test_promote_serial_lpc1_report_blocks_on_backpressure() -> None:
    variant = {
        "status": "ok",
        "top": "decoder_r64_k1_serial_rank_lpc1_wrapper",
        "lanes_per_cycle": 1,
        "metrics_row": {"status": "ok"},
    }
    focused = {
        "status": "ok",
        "expected": {"token": 5, "logit": 500},
        "observed": {"token": 5, "logit": 500, "tb_backpressure": 3},
    }

    report = build_report(
        serial_ranker={"variants": [variant]},
        service_compatibility={
            "recommendation": {"lowest_power_feasible": {"ranker": "serial_lpc1"}}
        },
        producer_replay={
            "replay_rows": [
                {
                    "lanes_per_cycle": 1,
                    "producer_ii_cycles": 384,
                    "rtl_sim": focused,
                }
            ]
        },
        focused_rtl_sim=focused,
        lanes_per_cycle=1,
        producer_ii_cycles=384,
    )

    assert report["decision"]["decision"] == "serial_lpc1_producer_coupled_wrapper_blocked"
    assert report["checks"][-1]["passed"] is False

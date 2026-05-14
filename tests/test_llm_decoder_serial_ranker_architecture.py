from npu.eval.probe_llm_decoder_serial_ranker_architecture import build_report


def test_serial_ranker_report_selects_best_timing_and_power_variants() -> None:
    report = build_report(
        variants=[
            {
                "top": "decoder_r64_k1_serial_rank_lpc1_wrapper",
                "lanes_per_cycle": 1,
                "tile_scan_cycles": 64,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "3.1",
                    "die_area": "810000",
                    "total_power_mw": "0.04",
                },
            },
            {
                "top": "decoder_r64_k1_serial_rank_lpc8_wrapper",
                "lanes_per_cycle": 8,
                "tile_scan_cycles": 8,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "4.5",
                    "die_area": "810000",
                    "total_power_mw": "0.02",
                },
            },
        ],
        sweep="runs/campaigns/npu/decoder_serial_ranker_architecture/sweeps/nangate45_r64_serial.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "serial_ranker_architecture_measured"
    assert report["best_timing_variant"]["lanes_per_cycle"] == 1
    assert report["lowest_power_variant"]["lanes_per_cycle"] == 8


def test_serial_ranker_report_blocks_without_metrics() -> None:
    report = build_report(
        variants=[
            {
                "top": "decoder_r64_k1_serial_rank_lpc4_wrapper",
                "lanes_per_cycle": 4,
                "tile_scan_cycles": 16,
                "metrics_row": {"status": "failed"},
            }
        ],
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "serial_ranker_architecture_blocked"
    assert report["best_timing_variant"] is None
    assert report["lowest_power_variant"] is None

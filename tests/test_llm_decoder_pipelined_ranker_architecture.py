from npu.eval.probe_llm_decoder_pipelined_ranker_architecture import build_report


def test_pipelined_ranker_report_selects_best_timing_variant() -> None:
    report = build_report(
        variants=[
            {
                "top": "decoder_r64_k1_rankseg8_pipe2_wrapper",
                "local_lanes": 8,
                "groups": 8,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "12.0",
                    "die_area": "810000",
                    "total_power_mw": "1.0",
                },
            },
            {
                "top": "decoder_r64_k1_rankseg16_pipe2_wrapper",
                "local_lanes": 16,
                "groups": 4,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "9.5",
                    "die_area": "810000",
                    "total_power_mw": "1.2",
                },
            },
        ],
        sweep="runs/campaigns/npu/decoder_pipelined_ranker_architecture/sweeps/nangate45_r64_pipe2.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "pipelined_ranker_architecture_measured"
    assert report["best_timing_variant"]["local_lanes"] == 16
    assert report["best_timing_variant"]["critical_path_ns"] == "9.5"


def test_pipelined_ranker_report_blocks_without_metrics() -> None:
    report = build_report(
        variants=[
            {
                "top": "decoder_r64_k1_rankseg8_pipe2_wrapper",
                "local_lanes": 8,
                "groups": 8,
                "metrics_row": {"status": "failed"},
            }
        ],
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "pipelined_ranker_architecture_blocked"
    assert report["best_timing_variant"] is None

from npu.eval.probe_llm_decoder_rank_tree_architecture import build_report


def test_rank_tree_report_selects_best_timing_variant() -> None:
    report = build_report(
        variants=[
            {
                "top": "decoder_r64_k1_ranktree_radix2_pipe6_wrapper",
                "radix": 2,
                "pipeline_stages": 6,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "5.2",
                    "die_area": "810000",
                    "total_power_mw": "0.7",
                },
            },
            {
                "top": "decoder_r64_k1_ranktree_radix4_pipe3_wrapper",
                "radix": 4,
                "pipeline_stages": 3,
                "metrics_row": {
                    "status": "ok",
                    "critical_path_ns": "4.8",
                    "die_area": "810000",
                    "total_power_mw": "0.5",
                },
            },
        ],
        sweep="runs/campaigns/npu/decoder_rank_tree_architecture/sweeps/nangate45_r64_ranktree.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "rank_tree_architecture_measured"
    assert report["best_timing_variant"]["radix"] == 4
    assert report["best_timing_variant"]["critical_path_ns"] == "4.8"


def test_rank_tree_report_blocks_without_metrics() -> None:
    report = build_report(
        variants=[
            {
                "top": "decoder_r64_k1_ranktree_radix4_pipe3_wrapper",
                "radix": 4,
                "pipeline_stages": 3,
                "metrics_row": {"status": "failed"},
            }
        ],
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "rank_tree_architecture_blocked"
    assert report["best_timing_variant"] is None

from npu.eval.probe_llm_decoder_output_projection_ranker_wrapper_physical import build_report


def _variant(*, lanes: int, metrics_status: str = "ok", sim_status: str = "ok") -> dict:
    return {
        "top": f"decoder_output_ranker_policy_r{lanes}_wrapper",
        "producer_lanes": lanes,
        "status": "ok",
        "simulations": {
            "serial": {"status": sim_status},
            "ranktree": {"status": sim_status},
        },
        "metrics_row": {
            "status": metrics_status,
            "critical_path_ns": "4.0",
            "die_area": "810000",
            "total_power_mw": "0.02",
        },
    }


def test_wrapper_physical_report_passes_when_all_variants_measured() -> None:
    report = build_report(
        variants=[_variant(lanes=64), _variant(lanes=128)],
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "output_projection_ranker_wrapper_physical_measured"
    assert report["target"]["producer_lanes"] == [64, 128]


def test_wrapper_physical_report_blocks_on_failed_sim() -> None:
    report = build_report(
        variants=[_variant(lanes=64, sim_status="vvp_failed")],
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "output_projection_ranker_wrapper_physical_incomplete"


def test_wrapper_physical_report_blocks_on_missing_metrics() -> None:
    report = build_report(
        variants=[_variant(lanes=64, metrics_status="failed")],
        sweep="sweep.json",
        make_target="3_3_place_gp",
    )

    assert report["decision"]["decision"] == "output_projection_ranker_wrapper_physical_incomplete"

from npu.eval.promote_llm_decoder_resident_ranktree_fallback import build_report


def _variant(*, simulation_status: str = "ok", metrics_status: str = "ok") -> dict:
    return {
        "status": "ok",
        "top": "decoder_r64_k1_ranktree_radix4_pipe3_wrapper",
        "design_dir": "runs/designs/activations/decoder_r64_k1_ranktree_radix4_pipe3_wrapper",
        "radix": 4,
        "pipeline_stages": 3,
        "simulation": {"status": simulation_status, "expected": {"token": 5, "logit": 500}},
        "metrics_row": {
            "status": metrics_status,
            "critical_path_ns": "4.35",
            "die_area": "810000",
            "total_power_mw": "0.011",
        },
        "synthesis": {"log_tail": ["[INFO GPL-1002] Placed Cell Area 32000.0"]},
    }


def _fallback_row(*, lanes: int, strategy: str, buffer_tiles: int = 0) -> dict:
    return {
        "producer": {
            "producer_lanes": lanes,
            "producer_ii_cycles": 2 if lanes == 64 else 3,
        },
        "recommended": {
            "strategy": strategy,
            "required_buffer_r64_tiles": buffer_tiles,
            "required_buffer_bytes": buffer_tiles * 128,
        },
    }


def _fallback(*rows: dict) -> dict:
    return {
        "recommendation": {
            "decision": "rank_tree_fallback_preferred_for_resident_weight",
            "unsafe_rows": len(rows),
            "rank_tree_recommended_rows": len(rows),
            "buffered_serial_recommended_rows": 0,
        },
        "fallback_rows": list(rows),
    }


def test_promotes_radix4_single_and_banked_ranktree_fallback() -> None:
    report = build_report(
        fallback=_fallback(
            _fallback_row(lanes=64, strategy="single_r64_ranktrees_ranktree_radix4"),
            _fallback_row(lanes=128, strategy="banked_r64_ranktrees_ranktree_radix4"),
        ),
        rank_tree={"variants": [_variant()]},
    )

    assert report["decision"]["decision"] == "resident_weight_ranktree_fallback_promoted"
    assert report["target"]["selected_radix"] == 4
    assert report["coverage"]["max_required_buffer_r64_tiles"] == 0
    assert report["selected_metrics"]["placed_cell_area_um2"] == 32000.0
    assert [row["mode"] for row in report["producer_modes"]] == [
        "single_r64_ranktree",
        "banked_r64_ranktrees",
    ]
    assert report["producer_modes"][1]["ranker_instances"] == 2
    assert report["producer_modes"][1]["ranker_total_power_mw"] == 0.022
    assert all(check["passed"] for check in report["checks"])


def test_blocks_when_ranktree_fallback_needs_waiting_buffer() -> None:
    report = build_report(
        fallback=_fallback(
            _fallback_row(
                lanes=64,
                strategy="single_r64_ranktrees_ranktree_radix4",
                buffer_tiles=1,
            )
        ),
        rank_tree={"variants": [_variant()]},
    )

    assert report["decision"]["decision"] == "resident_weight_ranktree_fallback_blocked"
    assert report["checks"][-1]["name"] == "promotion_requires_no_waiting_buffer"
    assert report["checks"][-1]["passed"] is False


def test_blocks_when_selected_ranktree_lacks_clean_simulation() -> None:
    report = build_report(
        fallback=_fallback(_fallback_row(lanes=64, strategy="single_r64_ranktrees_ranktree_radix4")),
        rank_tree={"variants": [_variant(simulation_status="failed")]},
    )

    assert report["decision"]["decision"] == "resident_weight_ranktree_fallback_blocked"
    assert report["checks"][3]["name"] == "selected_rank_tree_variant_has_clean_rtl_sim"
    assert report["checks"][3]["passed"] is False

from pathlib import Path

from npu.eval.estimate_llm_decoder_bf16_recoverability import build_report


def test_bf16_recoverability_report_quantifies_topk_contained_misses() -> None:
    report = build_report(
        sweep_path=Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json"),
        sample_file=Path("runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl"),
    )

    assert report["template"] == "grid_approx_pwl_bf16_path"
    assert report["sample_count"] == 48
    assert report["next_token_matches"] == 46
    assert report["topk_matches"] == 48
    assert report["diagnosis"]["topk_safe"]
    assert report["diagnosis"]["miss_count"] == 2
    assert report["diagnosis"]["decision"] in {
        "recoverable_margin_shift",
        "plausibly_recoverable_margin_shift",
        "topk_safe_but_recovery_unclear",
    }
    assert {miss["sample_id"] for miss in report["misses"]} == {
        "dist2_arith_three_plus_five",
        "dist2_sequence_months",
    }
    for miss in report["misses"]:
        assert miss["reference_rank_in_candidate_topk"] == 2
        assert miss["score_gap_to_flip_top1"] is not None
        assert miss["score_gap_to_flip_top1"] >= 0
        assert miss["recovery_class"] == "easy_rank2_below_median_margin"

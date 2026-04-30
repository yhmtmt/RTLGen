from pathlib import Path

from npu.eval.estimate_llm_decoder_quantization_outline import build_report


def test_decoder_quantization_outline_groups_comparable_dimensions() -> None:
    report = build_report(
        fp_sweep_path=Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json"),
        distribution_sweep_path=Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_distribution_robustness_v1.json"),
        q8_norm_frontier_path=Path("runs/datasets/llm_decoder_eval_tiny_v1/decoder_q8_norm_frontier__l2_decoder_q8_normalization_frontier_v1.json"),
    )

    by_dimension = {row["dimension"]: row for row in report["dimensions"]}
    assert by_dimension["logit_format"]["comparison_scope"] == "within_dimension_only"
    assert "grid_logits_bf16" in by_dimension["logit_format"]["summary"]["exact_safe_templates"]
    assert "grid_logits_q4" in by_dimension["logit_format"]["summary"]["topk_safe_only_templates"]
    assert "grid_prob_q8" in by_dimension["probability_output_format"]["summary"]["blocked_templates"]
    assert "grid_prob_bf16" in by_dimension["probability_output_format"]["summary"]["exact_safe_templates"]
    assert "grid_approx_pwl_bf16_path" in by_dimension["approximate_pwl_probability_path"]["summary"]["exact_safe_templates"]
    assert report["q8_norm_frontier"]["decision"]["selected_candidate"] == "grid_approx_pwl_bf16_path"
    assert any(
        row["template"] == "grid_approx_pwl_bf16_path"
        and row["rank_source"] == "measured_bf16_reciprocal_datapath_ppa"
        for row in report["q8_norm_frontier"]["measured_rows"]
    )
    assert any(
        row["template"] == "grid_approx_pwl_in_q8_w_q8_norm_exact"
        for row in report["q8_norm_frontier"]["measured_rows"]
    )

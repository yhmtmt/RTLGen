from pathlib import Path

from npu.eval.estimate_llm_decoder_survivor_cost import build_report


def test_decoder_survivor_cost_proxy_prefers_exact_safe_pwl_frontier() -> None:
    report = build_report(
        sweep_path=Path(
            "runs/datasets/llm_decoder_eval_tiny_v1/"
            "decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json"
        )
    )

    assert report["recommendation"]["template"] in {
        "grid_approx_pwl_bf16_path",
        "grid_approx_pwl_in_q8_w_q8_norm_exact",
    }
    assert report["cost_model"]["source"] == "hand_written_planning_proxy_not_literature_backed"
    assert report["cost_model"]["unit"] == "heuristic_planning_units"
    assert (
        report["cost_model"]["rtlgen_calibration_proposal"]
        == "prop_l1_decoder_normalization_arithmetic_calibration_v1"
    )
    ranked = report["ranked_candidates"]
    by_template = {row["template"]: row for row in ranked}

    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]["quality"]["eligible_for_cost_narrowing"]
    assert by_template["grid_approx_pwl_bf16_path"]["quality"]["eligible_for_cost_narrowing"]
    assert not by_template["grid_approx_pwl_in_q6_w_q6_norm_recip_q10"]["quality"]["eligible_for_cost_narrowing"]
    assert by_template["grid_prob_fp8_e5m2"]["quality"]["gate"] == "blocked_quality"
    assert (
        by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]["cost_proxy"]["relative_cost_units"]
        < by_template["grid_prob_bf16"]["cost_proxy"]["relative_cost_units"]
    )
    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]["cost_proxy"]["calibration_status"] == "uncalibrated"
    assert (
        by_template["grid_approx_pwl_bf16_path"]["cost_proxy"]["relative_cost_units"]
        < by_template["grid_prob_bf16"]["cost_proxy"]["relative_cost_units"]
    )

from pathlib import Path

from npu.eval.estimate_llm_decoder_pwl_frontier import build_report


def test_decoder_pwl_frontier_detail_keeps_bf16_primary_and_q8_alternate() -> None:
    report = build_report(
        sweep_path=Path(
            "runs/datasets/llm_decoder_eval_tiny_v1/"
            "decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json"
        ),
        cost_proxy_path=Path(
            "runs/datasets/llm_decoder_eval_tiny_v1/"
            "decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.json"
        ),
    )

    assert report["frontier_decision"]["primary_candidate"] == "grid_approx_pwl_bf16_path"
    assert report["frontier_decision"]["alternate_candidate"] == "grid_approx_pwl_in_q8_w_q8_norm_exact"
    assert report["frontier_decision"]["decision"] == "deepen_primary_keep_alternate"

    candidates = report["frontier_candidates"]
    assert {row["template"] for row in candidates} == {
        "grid_approx_pwl_bf16_path",
        "grid_approx_pwl_in_q8_w_q8_norm_exact",
    }
    by_template = {row["template"]: row for row in candidates}
    bf16 = by_template["grid_approx_pwl_bf16_path"]
    q8 = by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]

    assert bf16["quality"]["exact_safe"]
    assert q8["quality"]["exact_safe"]
    assert bf16["role"] == "primary_candidate"
    assert q8["role"] == "alternate_frontier"
    assert q8["lut_table"]["table_bits"] < bf16["lut_table"]["table_bits"]
    assert (
        q8["interpolate_datapath"]["multiplier_output_width_bits"]
        < bf16["interpolate_datapath"]["multiplier_output_width_bits"]
    )
    assert q8["normalization_path"]["integration_risk"] == "high"
    assert bf16["normalization_path"]["integration_risk"] == "medium"
    assert q8["normalization_path"]["relative_cost_units"] > bf16["normalization_path"]["relative_cost_units"]
    assert bf16["previous_survivor_cost_proxy"]["rank"] == 1
    assert q8["previous_survivor_cost_proxy"]["rank"] == 2

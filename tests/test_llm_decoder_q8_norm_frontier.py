from pathlib import Path

from npu.eval.estimate_llm_decoder_q8_norm_frontier import build_report
from npu.eval.sweep_llm_decoder_candidate_quality import _rough_grid_templates
from npu.eval.llm_decoder_quality import load_json


def test_q8_normalization_frontier_grid_contains_exact_reciprocal_and_bf16_anchor() -> None:
    model_contract = load_json(Path("runs/models/llm_decoder_tiny_v1/model_contract.json"))
    grid = _rough_grid_templates(model_contract, "decoder_q8_normalization_frontier_v1")

    assert set(grid) == {
        "candidate_onnx_softmax_exact",
        "grid_approx_pwl_bf16_path",
        "grid_approx_pwl_in_q8_w_q8_norm_exact",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q10",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q12",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q14",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q16",
    }
    assert grid["grid_approx_pwl_in_q8_w_q8_norm_exact"]["normalization_mode"] == "exact"
    assert grid["grid_approx_pwl_in_q8_w_q8_norm_recip_q12"]["normalization_mode"] == "reciprocal_quantized"
    assert grid["grid_approx_pwl_in_q8_w_q8_norm_recip_q12"]["normalization_reciprocal_bits"] == 12
    assert grid["grid_approx_pwl_bf16_path"]["normalization_reciprocal_float_format"] == "bf16"


def test_q8_normalization_frontier_report_selects_lowest_cost_exact_safe_reciprocal() -> None:
    report = build_report(sweep_path=Path("tests/fixtures/decoder_q8_norm_frontier_sweep.json"))

    assert report["decision"]["decision"] == "q8_reciprocal_candidate_survived"
    assert report["decision"]["selected_candidate"] == "grid_approx_pwl_in_q8_w_q8_norm_recip_q10"
    assert report["cost_model"]["source"] == "hand_written_planning_proxy_not_literature_backed"
    assert report["cost_model"]["unit"] == "heuristic_planning_units"
    assert (
        report["cost_model"]["rtlgen_calibration_proposal"]
        == "prop_l1_decoder_normalization_arithmetic_calibration_v1"
    )
    by_template = {row["template"]: row for row in report["ranked_rows"]}
    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["quality"]["exact_safe"]
    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["normalization"]["calibration_status"] == "uncalibrated"
    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q12"]["quality"]["exact_safe"]
    assert (
        by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["normalization"]["relative_cost_units"]
        < by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]["normalization"]["relative_cost_units"]
    )

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


def test_pwl_bitwidth_boundary_grid_narrows_integer_precision_floor() -> None:
    model_contract = load_json(Path("runs/models/llm_decoder_tiny_v1/model_contract.json"))
    grid = _rough_grid_templates(model_contract, "decoder_pwl_bitwidth_boundary_v1")

    assert set(grid) == {
        "candidate_onnx_softmax_exact",
        "grid_exact_logits_q13",
        "grid_exact_logits_q12",
        "grid_exact_logits_q11",
        "grid_exact_logits_q10",
        "grid_approx_pwl_float_norm_exact",
        "grid_approx_pwl_in_q13_w_q13_norm_exact",
        "grid_approx_pwl_in_q12_w_q12_norm_exact",
        "grid_approx_pwl_in_q11_w_q11_norm_exact",
        "grid_approx_pwl_in_q10_w_q10_norm_exact",
        "grid_approx_pwl_bf16_path",
    }
    assert grid["grid_approx_pwl_in_q11_w_q11_norm_exact"]["softmax_input_quant_bits"] == 11
    assert grid["grid_approx_pwl_in_q11_w_q11_norm_exact"]["softmax_weight_quant_bits"] == 11
    assert grid["grid_approx_pwl_in_q11_w_q11_norm_exact"]["normalization_mode"] == "exact"
    assert grid["grid_approx_pwl_bf16_path"]["normalization_reciprocal_float_format"] == "bf16"


def test_bf16_pwl_recovery_grid_adds_logit_tiebreak_variant() -> None:
    model_contract = load_json(Path("runs/models/llm_decoder_tiny_v1/model_contract.json"))
    grid = _rough_grid_templates(model_contract, "decoder_bf16_pwl_recovery_v1")

    assert set(grid) == {
        "candidate_onnx_softmax_exact",
        "grid_approx_pwl_bf16_path",
        "grid_approx_pwl_bf16_path_logit_tiebreak",
    }
    baseline = grid["grid_approx_pwl_bf16_path"]
    recovery = grid["grid_approx_pwl_bf16_path_logit_tiebreak"]
    assert baseline["normalization_reciprocal_float_format"] == "bf16"
    assert "score_tie_breaker" not in baseline
    assert recovery["normalization_reciprocal_float_format"] == "bf16"
    assert recovery["score_tie_breaker"] == "logit"


def test_bf16_pwl_scale_probe_grid_keeps_integer_controls() -> None:
    model_contract = load_json(Path("runs/models/llm_decoder_tiny_v1/model_contract.json"))
    grid = _rough_grid_templates(model_contract, "decoder_bf16_pwl_scale_probe_v1")

    assert set(grid) == {
        "candidate_onnx_softmax_exact",
        "grid_approx_pwl_bf16_path",
        "grid_approx_pwl_bf16_path_logit_tiebreak",
        "grid_approx_pwl_in_q12_w_q12_norm_exact",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q12",
    }
    assert grid["grid_approx_pwl_bf16_path_logit_tiebreak"]["score_tie_breaker"] == "logit"
    assert grid["grid_approx_pwl_in_q12_w_q12_norm_exact"]["normalization_mode"] == "exact"
    assert grid["grid_approx_pwl_in_q8_w_q8_norm_recip_q12"]["normalization_reciprocal_bits"] == 12


def test_q8_normalization_frontier_report_selects_lowest_cost_exact_safe_reciprocal() -> None:
    report = build_report(
        sweep_path=Path("tests/fixtures/decoder_q8_norm_frontier_sweep.json"),
        q8_recip_ppa_path=Path("tests/fixtures/q8_recip_norm_datapath_ppa.json"),
        q8_exact_ppa_path=Path("tests/fixtures/q8_exact_norm_datapath_ppa.json"),
        bf16_recip_ppa_path=Path("tests/fixtures/bf16_recip_norm_datapath_ppa.json"),
    )

    assert report["decision"]["decision"] == "measured_frontier_candidate_selected"
    assert report["decision"]["selected_candidate"] == "grid_approx_pwl_bf16_path"
    assert (
        report["cost_model"]["source"]
        == "rtlgen_openroad_q8_exact_q8_reciprocal_bf16_reciprocal_and_bf16_tie_rank_datapath_metrics"
    )
    assert report["cost_model"]["unit"] == "nangate45_physical_metrics"
    assert (
        report["cost_model"]["rtlgen_calibration_proposal"]
        == "prop_l1_decoder_q8_recip_norm_datapath_v1_and_prop_l1_softmax_rowwise_int8_r8_acc24_block_v1_and_prop_l1_decoder_bf16_recip_norm_datapath_v1_and_prop_l1_decoder_bf16_pwl_tie_rank_datapath_v1"
    )
    by_template = {row["template"]: row for row in report["ranked_rows"]}
    assert by_template["grid_approx_pwl_bf16_path"]["rank"] == 1
    assert (
        by_template["grid_approx_pwl_bf16_path"]["normalization"]["calibration_status"]
        == "integrated_bf16_reciprocal_datapath_measured"
    )
    assert (
        by_template["grid_approx_pwl_bf16_path"]["normalization"]["ppa_metrics"]["critical_path_ns"]
        == 4.2869
    )
    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["quality"]["exact_safe"]
    assert (
        by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["normalization"]["calibration_status"]
        == "integrated_q8_reciprocal_datapath_measured"
    )
    assert by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q12"]["quality"]["exact_safe"]
    assert (
        by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["normalization"]["ppa_metrics"]["critical_path_ns"]
        < by_template["grid_approx_pwl_in_q8_w_q8_norm_recip_q12"]["normalization"]["ppa_metrics"]["critical_path_ns"]
    )
    assert (
        by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]["normalization"]["calibration_status"]
        == "integrated_q8_exact_datapath_measured"
    )
    assert (
        by_template["grid_approx_pwl_in_q8_w_q8_norm_exact"]["normalization"]["ppa_metrics"]["critical_path_ns"]
        == 20.2712
    )


def test_q8_normalization_frontier_report_adds_recovered_bf16_tie_rank_cost() -> None:
    report = build_report(
        sweep_path=Path("tests/fixtures/decoder_q8_norm_frontier_recovery_sweep.json"),
        q8_recip_ppa_path=Path("tests/fixtures/q8_recip_norm_datapath_ppa.json"),
        q8_exact_ppa_path=Path("tests/fixtures/q8_exact_norm_datapath_ppa.json"),
        bf16_recip_ppa_path=Path("tests/fixtures/bf16_recip_norm_datapath_ppa.json"),
        bf16_tie_rank_ppa_path=Path("tests/fixtures/bf16_tie_rank_datapath_ppa.json"),
        bf16_recovery_path=Path("tests/fixtures/bf16_pwl_recovery_summary.json"),
    )

    assert report["decision"]["decision"] == "measured_frontier_candidate_selected"
    assert report["decision"]["selected_candidate"] == "grid_approx_pwl_bf16_path_logit_tiebreak"
    by_template = {row["template"]: row for row in report["ranked_rows"]}
    recovered = by_template["grid_approx_pwl_bf16_path_logit_tiebreak"]
    assert recovered["rank"] == 1
    assert recovered["role"] == "bf16_recovered_tie_rank_candidate"
    assert recovered["quality"]["exact_safe"]
    assert (
        recovered["normalization"]["rank_source"]
        == "measured_bf16_reciprocal_plus_score_tie_rank_ppa"
    )
    assert recovered["normalization"]["component_model"] == "additive_datapath_components"
    assert recovered["normalization"]["ppa_metrics"] == {
        "critical_path_ns": 7.5794,
        "die_area": 57476.735425,
        "total_power_mw": 0.01005,
    }
    assert recovered["normalization"]["component_ppa_metrics"]["score_tie_rank"]["critical_path_ns"] == 3.2925

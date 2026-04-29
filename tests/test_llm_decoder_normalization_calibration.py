from pathlib import Path

from npu.eval.calibrate_llm_decoder_normalization_cost import build_report


def test_decoder_normalization_calibration_uses_nangate45_l1_primitives() -> None:
    report = build_report()

    assert report["calibration_status"] == "partial_integer_reciprocal_primitives_calibrated"
    assert report["platform"] == "nangate45"
    selected = report["selected_primitives"]
    assert selected["q8_reciprocal_multiplier_16u"]["block_id"] == "mult16u_booth4_koggestone"
    assert selected["q8_reciprocal_multiplier_16u"]["platform"] == "nangate45"
    assert selected["q8_accumulator_adder_64u"]["block_id"] == "adder_koggestone_64u"
    assert selected["q8_accumulator_adder_64u"]["platform"] == "nangate45"


def test_decoder_normalization_calibration_keeps_reciprocal_ppa_tied_by_envelope() -> None:
    report = build_report()
    rows = {row["template"]: row for row in report["candidate_calibration"]}
    reciprocal_templates = [
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q10",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q12",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q14",
        "grid_approx_pwl_in_q8_w_q8_norm_recip_q16",
    ]

    reciprocal_sums = {tuple(sorted(rows[template]["primitive_sum_proxy"].items())) for template in reciprocal_templates}
    assert len(reciprocal_sums) == 1
    assert rows["grid_approx_pwl_in_q8_w_q8_norm_recip_q10"]["calibration_status"].startswith(
        "integer_reciprocal_primitives_calibrated"
    )
    assert "q10 remains a quality/minimum-precision choice" in "\n".join(report["interpretation"])


def test_decoder_normalization_calibration_marks_unmeasured_divider_and_bf16_gaps() -> None:
    report = build_report()
    rows = {row["template"]: row for row in report["candidate_calibration"]}

    q8_exact = rows["grid_approx_pwl_in_q8_w_q8_norm_exact"]
    assert q8_exact["calibration_status"] == "unmeasured_gap"
    assert "integer exact divider/reciprocal datapath" in q8_exact["unmeasured_gaps"]

    bf16 = rows["grid_approx_pwl_bf16_path"]
    assert bf16["calibration_status"] == "unmeasured_gap"
    assert "bf16 reciprocal path" in bf16["unmeasured_gaps"]


def test_decoder_normalization_calibration_script_sources_are_checked_in() -> None:
    report = build_report()
    for source in report["source_artifacts"].values():
        assert Path(source).exists()

from npu.eval.estimate_llm_decoder_attention_mixed_precision_quality import build_report


def test_attention_mixed_precision_quality_accepts_recip_lut_softmax_modes() -> None:
    report = build_report(
        dual_stream_feasibility=None,
        attention_heads=2,
        kv_heads=1,
        head_dim=8,
        sequence_length_list=[8],
        regime_list=["native_correlated_queries"],
        seed_count=1,
        candidate_specs=["q8:k8:v6:a24:s8:w8"],
        softmax_mode_list=["rtl_exact", "rtl_pow2sum", "rtl_recip_lut_q10", "rtl_recip_lut_q12"],
    )

    modes = {row["softmax_mode"] for row in report["candidate_summary"]}
    assert modes == {"rtl_exact", "rtl_pow2sum", "rtl_recip_lut_q10", "rtl_recip_lut_q12"}
    assert report["sweep_summary"]["candidate_count"] == 4
    assert report["sweep_summary"]["metric_row_count"] == 8
    assert "rtl_recip_lut_qN" in report["assumptions"][3]

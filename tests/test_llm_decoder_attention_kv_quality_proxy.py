from npu.eval.estimate_llm_decoder_attention_kv_quality_proxy import build_report


def _report():
    return build_report(
        quality_gate={"model": "quality_gate_fixture"},
        attention_heads=8,
        head_dim=8,
        sequence_length_list=[32],
        regime_list=["correlated_heads", "retrieval", "independent_heads"],
        seed_count=1,
        candidate_specs=["mha:kv8", "mha:kv4", "gqa8:kv8", "mqa:kv4"],
    )


def test_quality_proxy_keeps_mha_kv8_as_reference_pass() -> None:
    report = _report()
    mha8 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "mha_kv8")

    assert report["model"] == "llm_decoder_attention_kv_quality_proxy_v1"
    assert mha8["decision"] == "proxy_pass"
    assert mha8["mean_top1_match"] == 1.0
    assert mha8["mean_output_cosine"] > 0.999


def test_quality_proxy_marks_mqa_bound_only() -> None:
    report = _report()
    mqa4 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "mqa_kv4")

    assert mqa4["decision"] == "bound_only_retraining_required"
    assert mqa4["mean_output_cosine"] < 0.9


def test_quality_proxy_separates_head_sharing_from_kv_quantization() -> None:
    report = _report()
    mha4 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "mha_kv4")
    gqa8 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "gqa8_kv8")

    assert mha4["mean_output_cosine"] > gqa8["mean_output_cosine"]
    assert mha4["mean_top1_match"] > gqa8["mean_top1_match"]

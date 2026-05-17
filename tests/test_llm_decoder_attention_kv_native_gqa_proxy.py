from npu.eval.estimate_llm_decoder_attention_kv_native_gqa_proxy import build_report


def _report():
    return build_report(
        quality_proxy={"model": "quality_proxy_fixture"},
        attention_heads=8,
        head_dim=8,
        sequence_length_list=[32],
        regime_list=["native_correlated_queries", "native_retrieval", "native_low_margin"],
        seed_count=1,
        candidate_specs=["gqa8:kv8", "gqa8:kv4", "mqa:kv4"],
    )


def test_native_gqa_proxy_compares_against_same_sharing_reference() -> None:
    report = _report()
    gqa8 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "gqa8_kv8")

    assert report["model"] == "llm_decoder_attention_kv_native_gqa_proxy_v1"
    assert report["inputs"]["quality_proxy_model"] == "quality_proxy_fixture"
    assert gqa8["mean_output_cosine"] > 0.999
    assert gqa8["mean_top1_match"] > 0.99


def test_native_gqa_proxy_keeps_kv4_as_promising_or_risky() -> None:
    report = _report()
    gqa4 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "gqa8_kv4")

    assert gqa4["mean_output_cosine"] > 0.99
    assert gqa4["decision"] in {"native_lowbit_promising", "native_proxy_risk"}


def test_native_gqa_proxy_keeps_mqa_bound_separate() -> None:
    report = _report()
    mqa4 = next(row for row in report["candidate_summary"] if row["candidate_id"] == "mqa_kv4")

    assert mqa4["decision"] == "native_mqa_still_requires_model_evidence"

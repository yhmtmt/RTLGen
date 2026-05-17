from npu.eval.estimate_llm_decoder_attention_kv_trace_calibration import build_report


def _native_proxy():
    return {
        "model": "native_proxy_fixture",
        "candidate_summary": [
            {
                "candidate_id": "gqa8_kv4",
                "decision": "native_lowbit_promising",
                "mean_top1_match": 0.992,
                "mean_output_cosine": 0.996,
                "mean_output_rmse": 0.02,
            },
            {
                "candidate_id": "gqa8_kv8",
                "decision": "native_proxy_risk",
                "mean_top1_match": 0.995,
                "mean_output_cosine": 0.9999,
                "mean_output_rmse": 0.001,
            },
        ],
        "regime_summary": [
            {
                "candidate_id": "gqa8_kv4",
                "regime": "native_low_margin",
                "mean_top1_match": 0.977,
                "mean_output_cosine": 0.993,
            }
        ],
    }


def _quality_compare(mean_delta: float = 0.002, max_delta: float = 0.02):
    return {
        "dataset_id": "fixture_dataset",
        "candidate_semantics": "onnx_logits_fp_softmax_exact_norm_exact_prob_fp",
        "aggregate": {
            "sample_count": 1,
            "next_token_id_match_rate": 1.0,
            "topk_contains_reference_id_rate": 1.0,
            "distribution": {
                "reference_top1_top2_logit_margin_min": 0.1,
                "reference_top1_top2_logit_margin_mean": 1.0,
                "candidate_top1_top2_score_margin_min": 0.01,
                "candidate_top1_top2_score_margin_mean": 0.2,
            },
        },
        "samples": [
            {
                "sample_id": "s0",
                "selected_tensor_trace": {
                    "compared_tensors": [
                        {
                            "name": "present.0.key",
                            "deltas": {
                                "mean_abs_delta": mean_delta,
                                "max_abs_delta": max_delta,
                                "std_abs_delta": 0.01,
                            },
                            "candidate_quantization": {"bits": 4, "scale": 0.5, "max_abs": 3.5},
                        },
                        {
                            "name": "present.0.value",
                            "deltas": {
                                "mean_abs_delta": mean_delta,
                                "max_abs_delta": max_delta,
                                "std_abs_delta": 0.01,
                            },
                            "candidate_quantization": {"bits": 4, "scale": 0.4, "max_abs": 2.8},
                        },
                    ]
                },
            }
        ],
    }


def test_trace_calibration_advances_when_native_proxy_and_real_traces_are_in_family() -> None:
    report = build_report(
        native_gqa_proxy=_native_proxy(),
        quality_compare_inputs=[("gpt2", "/tmp/gpt2.json", _quality_compare())],
    )

    assert report["model"] == "llm_decoder_attention_kv_trace_calibration_v1"
    assert report["decision"]["status"] == "advance_model_native_gqa_kv4_quality_run"
    assert report["trained_checkpoint_trace_records"][0]["trace_rollup"]["tensor_count"] == 2
    assert report["decision"]["cautions"]


def test_trace_calibration_blocks_large_kv4_trace_delta() -> None:
    report = build_report(
        native_gqa_proxy=_native_proxy(),
        quality_compare_inputs=[("gpt2", "/tmp/gpt2.json", _quality_compare(mean_delta=0.04, max_delta=0.1))],
    )

    assert report["decision"]["status"] == "hold_for_kv4_recovery"
    assert report["decision"]["blockers"]

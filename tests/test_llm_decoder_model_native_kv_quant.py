from npu.eval.evaluate_llm_decoder_model_native_kv_quant import _decision, _summarize_rows


def test_summarize_rows_records_rank_and_logit_metrics() -> None:
    rows = [
        {
            "top1_match": 1.0,
            "topk_contains": 1.0,
            "logit_cosine": 0.9999,
            "probability_kl": 0.0001,
            "reference_margin": 0.1,
            "max_abs_logit_delta": 0.02,
        },
        {
            "top1_match": 0.0,
            "topk_contains": 1.0,
            "logit_cosine": 0.998,
            "probability_kl": 0.001,
            "reference_margin": 0.01,
            "max_abs_logit_delta": 0.05,
        },
    ]

    summary = _summarize_rows(rows)

    assert summary["comparison_count"] == 2
    assert summary["top1_match_rate"] == 0.5
    assert summary["topk_contains_rate"] == 1.0
    assert summary["min_reference_margin"] == 0.01
    assert summary["max_abs_logit_delta_max"] == 0.05


def test_decision_advances_when_native_checkpoint_kv4_rankings_hold() -> None:
    decision = _decision(
        [
            {"kv_bits": 8, "top1_match_rate": 1.0, "topk_contains_rate": 1.0, "mean_logit_cosine": 0.99999},
            {"kv_bits": 4, "top1_match_rate": 0.99, "topk_contains_rate": 1.0, "mean_logit_cosine": 0.9995},
        ],
        expected_gqa_group_size=8,
        actual_gqa_group_size=8.0,
    )

    assert decision["status"] == "native_checkpoint_kv4_promising"
    assert decision["blockers"] == []


def test_decision_marks_non_tensor_kv4_granularity_as_recovery_candidate() -> None:
    decision = _decision(
        [
            {
                "kv_bits": 4,
                "kv_granularity": "tensor",
                "top1_match_rate": 0.75,
                "topk_contains_rate": 0.9,
                "mean_logit_cosine": 0.98,
                "mean_probability_kl": 0.2,
            },
            {
                "kv_bits": 4,
                "kv_granularity": "token_vector",
                "top1_match_rate": 1.0,
                "topk_contains_rate": 1.0,
                "mean_logit_cosine": 0.9999,
                "mean_probability_kl": 0.0001,
            },
        ],
        expected_gqa_group_size=8,
        actual_gqa_group_size=8.0,
    )

    assert decision["status"] == "kv4_granularity_recovery_promising"
    assert decision["selected_kv4_granularity"] == "token_vector"
    assert decision["blockers"] == []


def test_decision_blocks_wrong_gqa_group_or_kv4_rank_regression() -> None:
    decision = _decision(
        [
            {"kv_bits": 8, "top1_match_rate": 1.0, "topk_contains_rate": 1.0, "mean_logit_cosine": 0.99999},
            {"kv_bits": 4, "top1_match_rate": 0.9, "topk_contains_rate": 0.95, "mean_logit_cosine": 0.9995},
        ],
        expected_gqa_group_size=8,
        actual_gqa_group_size=4.0,
    )

    assert decision["status"] == "hold_for_qat_or_safer_kv_format"
    assert any("model_gqa_group_size" in blocker for blocker in decision["blockers"])
    assert any("KV4 candidate changed too many" in blocker for blocker in decision["blockers"])

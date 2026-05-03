import json
from pathlib import Path

from npu.eval.run_llm_decoder_onnx_candidate import _select_next_token_id, _topk_pairs
from npu.eval.summarize_llm_decoder_bf16_pwl_recovery import build_report


def test_logit_tiebreak_changes_only_equal_score_ranking() -> None:
    scores = [0.4, 0.4, 0.3]
    logits = [1.0, 2.0, 9.0]

    assert _select_next_token_id(scores) == 0
    assert _select_next_token_id(scores, tie_break_values=logits) == 1
    assert list(_topk_pairs(scores, k=3, tie_break_values=logits)) == [
        (1, 0.4),
        (0, 0.4),
        (2, 0.3),
    ]


def test_bf16_pwl_recovery_summary_detects_exact_safe_tiebreak(tmp_path: Path) -> None:
    sweep = {
        "templates": [
            {
                "template": "grid_approx_pwl_bf16_path",
                "candidate_semantics": "baseline",
                "sample_count": 4,
                "next_token_id_match_rate": 0.5,
                "topk_contains_reference_id_rate": 1.0,
                "next_token_mismatch_sample_ids": ["a", "b"],
                "topk_miss_sample_ids": [],
            },
            {
                "template": "grid_approx_pwl_bf16_path_logit_tiebreak",
                "candidate_semantics": "recovered",
                "score_tie_breaker": "logit",
                "sample_count": 4,
                "next_token_id_match_rate": 1.0,
                "topk_contains_reference_id_rate": 1.0,
                "next_token_mismatch_sample_ids": [],
                "topk_miss_sample_ids": [],
            },
        ],
    }
    sweep_path = tmp_path / "sweep.json"
    sweep_path.write_text(json.dumps(sweep), encoding="utf-8")

    report = build_report(sweep_path=sweep_path)

    assert report["diagnosis"]["decision"] == "tie_break_recovery_sufficient"
    assert report["diagnosis"]["exact_safe_after_recovery"]
    assert report["recovered_sample_ids"] == ["a", "b"]
    assert report["regression_sample_ids"] == []

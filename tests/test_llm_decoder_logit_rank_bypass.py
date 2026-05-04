import json
from pathlib import Path

from npu.eval.summarize_llm_decoder_logit_rank_bypass import build_report


def test_logit_rank_bypass_report_marks_exact_safe_and_scope(tmp_path: Path) -> None:
    sweep = tmp_path / "sweep.json"
    sweep.write_text(
        json.dumps(
            {
                "rough_grid": "decoder_logit_rank_bypass_v1",
                "task": "greedy_next_token",
                "templates": [
                    {
                        "template": "candidate_onnx_softmax_exact",
                        "sample_count": 2,
                        "next_token_id_match_rate": 1.0,
                        "topk_contains_reference_id_rate": 1.0,
                        "next_token_mismatch_sample_ids": [],
                        "topk_miss_sample_ids": [],
                    },
                    {
                        "template": "candidate_onnx_logit_rank_bypass",
                        "sample_count": 2,
                        "next_token_id_match_rate": 1.0,
                        "topk_contains_reference_id_rate": 1.0,
                        "next_token_mismatch_sample_ids": [],
                        "topk_miss_sample_ids": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(sweep_path=sweep, rank_ppa_path=None)

    assert report["decision"]["decision"] == "logit_rank_bypass_exact_safe"
    assert report["decision"]["selected_candidate"] == "candidate_onnx_logit_rank_bypass"
    assert report["quality"]["logit_rank_bypass"]["next_token_matches"] == 2
    assert "temperature_sampling" in report["bypass_scope"]["not_valid_for"]
    assert "reciprocal_normalization" in report["bypass_scope"]["removed_datapaths"]
    assert report["rank_datapath_proxy"]["status"] == "missing_rank_ppa"

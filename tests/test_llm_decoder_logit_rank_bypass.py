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
    assert report["rank_datapath_ppa"]["status"] == "missing_rank_ppa"


def test_logit_rank_bypass_report_uses_measured_logit_rank_ppa(tmp_path: Path) -> None:
    sweep = tmp_path / "sweep.json"
    sweep.write_text(
        json.dumps(
            {
                "rough_grid": "decoder_logit_rank_bypass_v1",
                "task": "greedy_next_token",
                "templates": [
                    {
                        "template": "candidate_onnx_softmax_exact",
                        "sample_count": 1,
                        "next_token_id_match_rate": 1.0,
                        "topk_contains_reference_id_rate": 1.0,
                    },
                    {
                        "template": "candidate_onnx_logit_rank_bypass",
                        "sample_count": 1,
                        "next_token_id_match_rate": 1.0,
                        "topk_contains_reference_id_rate": 1.0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    ppa = tmp_path / "l1_decoder_logit_rank_datapath_v1_r2.json"
    ppa.write_text(
        json.dumps(
            {
                "item_id": "l1_decoder_logit_rank_datapath_v1_r2",
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k1_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 3.1833,
                            "die_area": 3738.711025,
                            "total_power_mw": 0.00348,
                        },
                    },
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k4_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 3.6015,
                            "die_area": 8605.345225,
                            "total_power_mw": 0.0164,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(sweep_path=sweep, rank_ppa_path=ppa)

    proxy = report["rank_datapath_ppa"]
    assert proxy["status"] == "measured_logit_rank_datapath"
    assert proxy["argmax_ppa"]["role"] == "argmax_k1"
    assert proxy["topk_ppa"]["role"] == "topk_k4"
    assert proxy["argmax_ppa"]["metrics"]["die_area"] == 3738.711025
    assert proxy["topk_ppa"]["metrics"]["die_area"] == 8605.345225

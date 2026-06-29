import argparse
import csv
import json

from npu.eval.audit_llm_decoder_attention_mixed_int8_quality_energy_frontier import build_payload


def _write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_metrics(path, *, design, critical_path_ns, die_area, power_mw):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "design",
                "platform",
                "status",
                "critical_path_ns",
                "die_area",
                "total_power_mw",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "design": design,
                "platform": "nangate45",
                "status": "ok",
                "critical_path_ns": critical_path_ns,
                "die_area": die_area,
                "total_power_mw": power_mw,
            }
        )
    return path


def test_build_payload_selects_quality_backed_fp16_softmax_proxy(tmp_path):
    quality_frontier = _write_json(
        tmp_path / "quality_frontier.json",
        {
            "diagnosis": {
                "quality_passing_candidate_ids": ["qkv8_float_exact"],
                "quality_best_candidate_id": "qkv8_float_exact",
                "quality_best_top1_match_rate": 1.0,
                "quality_best_mean_probability_kl": 0.0012,
            }
        },
    )
    score_recovery = _write_json(
        tmp_path / "score_recovery.json",
        {
            "candidate_summaries": [
                {
                    "candidate_id": "score32_float",
                    "decision_status": "mixed_int8_native_attention_shadow_hold",
                    "top1_match_rate": 0.984375,
                    "topk_contains_rate": 1.0,
                    "mean_probability_kl": 0.0017,
                },
                {
                    "candidate_id": "qkv8_q24_pwl_recip_q24_bucket8",
                    "decision_status": "mixed_int8_native_attention_shadow_hold",
                    "top1_match_rate": 0.96875,
                    "topk_contains_rate": 1.0,
                    "mean_probability_kl": 0.0132,
                },
            ]
        },
    )
    exact_div = _write_json(
        tmp_path / "exact_div.json",
        {
            "diagnosis": {
                "decision": "score32_exact_div_feasible",
                "best_feasible_latency_us": 12.3,
            },
            "best_feasible": {
                "precision_profile": "score32_w16_exact_div",
                "replica_recost_latency_us": 12.3,
                "replica_recost_area_fit_replica_count": 2,
            },
        },
    )
    exact_div_split2 = _write_json(
        tmp_path / "exact_div_split2.json",
        {
            "diagnosis": {
                "decision": "score32_exact_div_split2_feasible",
                "best_feasible_latency_us": 9.8,
            },
            "best_requested": {
                "precision_profile": "score32_w16_exact_div_split2",
                "replica_recost_latency_us": 9.8,
                "replica_recost_area_fit_replica_count": 4,
            },
        },
    )
    nm1_metrics = _write_metrics(
        tmp_path / "nm1.csv",
        design="npu_fp16_cpp_nm1_softmaxcmp",
        critical_path_ns=5.69,
        die_area=2250000.0,
        power_mw=0.184,
    )
    nm2_metrics = _write_metrics(
        tmp_path / "nm2.csv",
        design="npu_fp16_cpp_nm2_softmaxcmp",
        critical_path_ns=5.47,
        die_area=2250000.0,
        power_mw=0.189,
    )

    payload = build_payload(
        argparse.Namespace(
            quality_backed_frontier_json=quality_frontier,
            score_precision_recovery_json=score_recovery,
            exact_div_recost_json=exact_div,
            exact_div_split2_recost_json=exact_div_split2,
            fp16_softmax_nm1_metrics=nm1_metrics,
            fp16_softmax_nm2_metrics=nm2_metrics,
        )
    )

    assert payload["decision"] == "mixed_int8_quality_energy_frontier_composed_measurement_required"
    assert payload["quality_gate"]["qkv8_float_exact"]["quality_backed"] is True
    assert payload["quality_gate"]["score32_float"]["top1_match_rate"] == 0.984375
    assert payload["quality_gate"]["qkv8_q24_pwl_recip_q24_bucket8"]["top1_match_rate"] == 0.96875
    assert (
        payload["best_fp16_softmax_proxy_candidate"]["candidate_id"]
        == "qkv8_float_exact_fp16_softmax_nm2_proxy"
    )
    assert len(payload["measured_non_quality_backed_recosts"]) == 2
    assert payload["diagnosis"]["non_quality_backed_measured_recost_count"] == 2

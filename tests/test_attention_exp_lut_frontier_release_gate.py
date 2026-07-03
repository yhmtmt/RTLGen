from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from npu.eval.check_attention_exp_lut_frontier_release import build_payload


def _quality_payload(*, status: str = "mixed_int8_generation_quality_pass", candidate_id: str = "score32_exp_lut_div"):
    return {
        "quality_gate": "mixed_int8_generation_quality",
        "candidate_summary": {
            "candidate_id": candidate_id,
            "decision_status": status,
            "teacher_forced_mean_nll_delta": 0.05,
            "teacher_forced_candidate_reference_token_prob_mean": 0.44,
            "free_run_token_match_rate": 0.875,
            "q_bits": 8,
            "k_bits": 8,
            "v_bits": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "softmax_mode": "exp_lut_div_bucket20",
        },
        "precision": {
            "candidate_id": candidate_id,
            "q_bits": 8,
            "k_bits": 8,
            "v_bits": 8,
            "score_bits": 32,
            "weight_bits": 16,
            "softmax_mode": "exp_lut_div_bucket20",
        },
        "decision": {
            "status": status,
            "thresholds": {
                "teacher_forced_mean_nll_delta_max": 0.4,
                "teacher_forced_candidate_reference_token_prob_mean_min": 0.1,
                "free_running_match_rate_min": 0.75,
            },
        },
    }


def _config_payload():
    return {
        "top_name": "attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20",
        "attention_dual_stream_composed": {
            "softmax_score_bits": 32,
            "softmax_weight_bits": 16,
            "softmax_reciprocal_lut_bucket_shift": 20,
            "value_bits": 8,
            "softmax_impl": "exp_lut_div",
            "semantic_profile": "score32_exp_lut_div",
            "equivalence_hash": False,
        },
    }


def _write_inputs(tmp_path: Path, *, quality=None, config=None, metrics_text: str | None = None):
    quality_path = tmp_path / "quality.json"
    config_path = tmp_path / "config.json"
    metrics_path = tmp_path / "metrics.csv"
    quality_path.write_text(__import__("json").dumps(quality or _quality_payload()) + "\n", encoding="utf-8")
    config_path.write_text(__import__("json").dumps(config or _config_payload()) + "\n", encoding="utf-8")
    design = _config_payload()["top_name"]
    metrics_path.write_text(
        metrics_text
        or (
            "design,status,critical_path_ns,instance_area_um2,stdcell_area_um2,total_power_mw,param_hash,tag\n"
            f"{design},ok,9.75,360000,360000,8.2,abc123,exp_lut\n"
        ),
        encoding="utf-8",
    )
    return quality_path, metrics_path, config_path


def _args(quality_path: Path, metrics_path: Path, config_path: Path) -> Namespace:
    return Namespace(
        quality_json=quality_path,
        metrics_csv=metrics_path,
        config_json=config_path,
        expected_candidate_id="score32_exp_lut_div",
        expected_bucket_shift=20,
    )


def test_exp_lut_frontier_release_gate_passes_matching_quality_and_ppa(tmp_path: Path) -> None:
    quality_path, metrics_path, config_path = _write_inputs(tmp_path)

    payload = build_payload(_args(quality_path, metrics_path, config_path))

    assert payload["release_ready"] is True
    assert payload["failures"] == []
    assert payload["quality"]["candidate_id"] == "score32_exp_lut_div"
    assert payload["config"]["semantic_profile"] == "score32_exp_lut_div"
    assert payload["metrics"]["ok_row_count"] == 1


def test_exp_lut_frontier_release_gate_rejects_quality_hold(tmp_path: Path) -> None:
    quality_path, metrics_path, config_path = _write_inputs(
        tmp_path,
        quality=_quality_payload(status="mixed_int8_generation_quality_hold"),
    )

    payload = build_payload(_args(quality_path, metrics_path, config_path))

    assert payload["release_ready"] is False
    assert any("quality decision status" in failure for failure in payload["failures"])


def test_exp_lut_frontier_release_gate_rejects_wrong_wrapper_profile(tmp_path: Path) -> None:
    config = _config_payload()
    config["attention_dual_stream_composed"]["semantic_profile"] = "score32_w16_recip_lut_q16"
    quality_path, metrics_path, config_path = _write_inputs(tmp_path, config=config)

    payload = build_payload(_args(quality_path, metrics_path, config_path))

    assert payload["release_ready"] is False
    assert any("semantic_profile" in failure for failure in payload["failures"])

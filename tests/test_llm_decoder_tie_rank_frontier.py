from pathlib import Path

from npu.eval.estimate_llm_decoder_tie_rank_frontier import build_report


def test_gpt2_tie_rank_frontier_uses_measured_component_ppa() -> None:
    report = build_report(
        recovery_path=Path(
            "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
            "decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json"
        ),
        bf16_recip_ppa_path=Path("control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json"),
        bf16_tie_rank_ppa_path=Path(
            "control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json"
        ),
    )

    assert report["decision"]["decision"] == "hardware_recovery_plausible"
    assert report["decision"]["selected_candidate"] == "grid_approx_pwl_bf16_path_logit_tiebreak"
    assert report["quality"]["baseline"]["next_token_matches"] == 94
    assert report["quality"]["recovery"]["next_token_matches"] == 96
    assert report["quality"]["recovered_sample_ids"] == [
        "gpt2_stress_geo_australia_capital",
        "gpt2_stress_math_four_times_five",
    ]
    assert report["quality"]["regression_sample_ids"] == []
    assert report["components"]["recovered_path"]["component_model"] == "conservative_additive_datapath_components"
    assert report["components"]["recovered_path"]["metrics"] == {
        "critical_path_ns": 7.5794,
        "die_area": 57476.735425,
        "total_power_mw": 0.01005,
    }
    assert (
        report["components"]["recovered_path"]["incremental_vs_bf16_reciprocal"]["critical_path_ns"][
            "relative_percent"
        ]
        == 76.804
    )

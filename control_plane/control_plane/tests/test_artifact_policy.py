from control_plane.artifact_policy import is_transportable_expected_output


def test_transportable_expected_output_allows_generated_campaign_json() -> None:
    assert is_transportable_expected_output(
        "runs/campaigns/npu/demo_campaign/campaign__l2_demo_campaign.json"
    )


def test_transportable_expected_output_rejects_campaign_artifacts_dir() -> None:
    assert not is_transportable_expected_output(
        "runs/campaigns/npu/demo_campaign__l2_demo_campaign/artifacts/mapper/x/schedule.yml"
    )


def test_transportable_expected_output_allows_compact_attention_kv_dataset() -> None:
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_memory__l2_decoder_attention_kv_memory_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_capacity_noc__l2_decoder_attention_kv_capacity_noc_baseline_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_noc_scheduler__l2_decoder_attention_kv_noc_scheduler_selected_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_spill_scheduler__l2_decoder_attention_kv_spill_scheduler_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_hbm_controller__l2_decoder_attention_kv_hbm_controller_llama7b_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_physical_hbm_frontier__"
        "l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_physical_hbm_quality_backed__"
        "l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_physical_hbm_memory_noc__"
        "l2_decoder_attention_kv_physical_hbm_memory_noc_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_physical_hbm_compute_sensitivity__"
        "l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_compute_floor_gap__"
        "l2_decoder_attention_kv_compute_floor_gap_llama7b_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_compute_ceiling_envelope__"
        "l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_quality_gate__l2_decoder_attention_kv_quality_gate_llama7b_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_quality_proxy__l2_decoder_attention_kv_quality_proxy_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_native_gqa_proxy__l2_decoder_attention_kv_native_gqa_proxy_llama7b_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_trace_calibration__l2_decoder_attention_kv_trace_calibration_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_model_native_quality__l2_decoder_attention_kv_model_native_quality_tinyllama_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_model_native_recovery__l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_mixed_int8_broad_native_quality__"
        "l2_decoder_attention_mixed_int8_broad_native_quality_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_mixed_int8_high_score_boundary__"
        "l2_decoder_attention_mixed_int8_high_score_boundary_llama7b_v1.md"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule__"
        "l2_decoder_attention_kv_dense_tile_endpoint_measured_l1_clustered_schedule_llama7b_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json"
    )
    assert is_transportable_expected_output(
        "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
        "decoder_attention_noc_profile__l2_decoder_attention_noc_profile_v1.md"
    )


def test_transportable_expected_output_allows_operational_component_frontier() -> None:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_operational_component_frontier__"
        "l2_decoder_attention_operational_component_frontier_llama7b_v1"
    )

    assert is_transportable_expected_output(f"{base}{stem}.json")
    assert is_transportable_expected_output(f"{base}{stem}.md")


def test_transportable_expected_output_allows_decode_score_tile_equivalence() -> None:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_tile_equivalence__"
        "l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1"
    )

    assert is_transportable_expected_output(f"{base}{stem}.json")
    assert is_transportable_expected_output(f"{base}{stem}.md")


def test_transportable_expected_output_allows_decode_score_local_cluster_equivalence() -> None:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_local_cluster_equivalence__"
        "l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1"
    )

    assert is_transportable_expected_output(f"{base}{stem}.json")
    assert is_transportable_expected_output(f"{base}{stem}.md")


def test_transportable_expected_output_allows_decode_score_multivalue_cluster_equivalence() -> None:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_multivalue_cluster_equivalence__"
        "l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1"
    )

    assert is_transportable_expected_output(f"{base}{stem}.json")
    assert is_transportable_expected_output(f"{base}{stem}.md")


def test_transportable_expected_output_allows_decode_score_multivalue_gqa_group_equivalence() -> None:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_multivalue_gqa_group_equivalence__"
        "l2_decoder_attention_decode_score_multivalue_gqa_group_equivalence_llama7b_v1"
    )

    assert is_transportable_expected_output(f"{base}{stem}.json")
    assert is_transportable_expected_output(f"{base}{stem}.md")


def test_transportable_expected_output_allows_decode_score_multivalue_gqa_folded_lane_equivalence() -> None:
    base = "runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/"
    stem = (
        "decoder_attention_decode_score_multivalue_gqa_folded_lane_equivalence__"
        "l2_decoder_attention_decode_score_multivalue_gqa8_folded_lane_equivalence_llama7b_v1"
    )

    assert is_transportable_expected_output(f"{base}{stem}.json")
    assert is_transportable_expected_output(f"{base}{stem}.md")

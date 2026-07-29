## Summary
- item_id: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7`
- run_key: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7_run_50d9a1f334d61ef6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `6ae44a18be7e187e1f0e53eb04d50574d09091d3`
- review_metadata_source_commit: `4676970c2b1c3ca5bec73819797a0ab290cb4de6`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence`
- comparison_role: `equivalence_check`
- expected_direction: `prove_full_composed_equivalence_or_diagnose`
- expected_reason: `Only a complete structured-row and protocol pass with canonical global-sidecar packing can promote this composed path into the measured Llama7B architecture model.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence__l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Does the fully composed producer-to-SRAM-to-local/global RTL path produce every expected cluster and root row while satisfying exact traffic counts and all ready-valid, residency, cadence, and release invariants?`
- comparison_role: `equivalence_check`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence__l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

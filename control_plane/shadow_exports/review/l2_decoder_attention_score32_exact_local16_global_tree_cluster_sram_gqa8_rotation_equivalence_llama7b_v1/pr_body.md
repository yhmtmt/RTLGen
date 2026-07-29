## Summary
- item_id: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_run_0f84db5a230c6295`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c2557fcbd4f09e6be70296988e6c28a0dbeeb38a`
- review_metadata_source_commit: `c2557fcbd4f09e6be70296988e6c28a0dbeeb38a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence`
- comparison_role: `equivalence_check`
- expected_direction: `prove_four_group_rotation_equivalence_or_diagnose`
- expected_reason: `The full Llama7B score32 hierarchy should not be recosted from a single-head-group proof alone.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence__l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Does the composed producer-to-SRAM-to-finalized-tree RTL path remain exact when the four logical head groups run sequentially for 32 wave commands with rotated command/head metadata and group-specific block ownership?`
- comparison_role: `equivalence_check`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence__l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

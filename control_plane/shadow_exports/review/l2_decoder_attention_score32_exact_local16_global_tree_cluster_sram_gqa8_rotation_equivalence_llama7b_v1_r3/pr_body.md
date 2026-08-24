## Summary
- item_id: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r3`
- run_key: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r3_run_9657995e51c127e3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r3/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r3.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_gqa8_full_head_dimension_revision_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `36c98fa0866aade221bc3afe21fd1fd66b3aedd2`
- review_metadata_source_commit: `f60f96e0687e9927993570c59de8a40c3de4637f`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence`
- comparison_role: `corrective_equivalence_check`
- expected_direction: `prove_full_head_gqa8_rotation_or_diagnose`
- expected_reason: `The r2 serial replay exhausted the aggregate wall-time bound without a mismatch; r3 must preserve exact four-group coverage with three bounded independent producer replays.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence__l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r3.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Does the previously selected score32 GQA8 hierarchy remain exact when the producer sequential dependency spans the full 128-dimensional Llama7B query/key dot product?`
- comparison_role: `corrective_equivalence_check`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence__l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1_r3.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

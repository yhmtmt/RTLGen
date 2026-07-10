## Summary
- item_id: `l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1_run_04a9ff06d7526af6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1e00b8d5a1e74eb8fc9b7209b844b609844e6a43`
- review_metadata_source_commit: `1e00b8d5a1e74eb8fc9b7209b844b609844e6a43`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_two_pass_global_max_equivalence`
- comparison_role: `semantic_equivalence_gate`
- expected_direction: `prove_two_pass_attention_equivalence`
- expected_reason: `Full-model PPA recost remains ineligible until the scalable normalization path is embodied and exact.`
- expectation_status: `unspecified`
- evaluation_summary: `Two-pass attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_global_max_equivalence__l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; block_counts=[4, 8]; command_count=3; scenarios=['always_ready', 'result_backpressure']; gates={'exact_exp_sum': True, 'exact_global_max': True, 'exact_ready_valid_schedule': True, 'exact_weighted_value': True}; remaining_abstractions=['bounded internal score/value registers must be replaced with measured score-SRAM and KV replay ports', 'final divider lane folding and full 16384-block scheduling require physical exploration'].`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `semantic_equivalence_gate`
- proposal_outcome: `attention_two_pass_equivalence_pass`
- comparison_summary: `Two-pass attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_global_max_equivalence__l2_decoder_attention_two_pass_global_max_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; block_counts=[4, 8]; command_count=3; scenarios=['always_ready', 'result_backpressure']; gates={'exact_exp_sum': True, 'exact_global_max': True, 'exact_ready_valid_schedule': True, 'exact_weighted_value': True}; remaining_abstractions=['bounded internal score/value registers must be replaced with measured score-SRAM and KV replay ports', 'final divider lane folding and full 16384-block scheduling require physical exploration'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

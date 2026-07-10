## Summary
- item_id: `l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1`
- run_key: `l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1_run_103d4896d0c3ea53`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `7dd3b32a12c2dcc4acc528aa88dd71fd3d88ad12`
- review_metadata_source_commit: `7dd3b32a12c2dcc4acc528aa88dd71fd3d88ad12`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_hierarchical_softmax_architecture`
- comparison_role: `hierarchical_composition_gate`
- expected_direction: `select_scalable_softmax_composition`
- expected_reason: `Do not extrapolate locally normalized 8-token outputs into a full Llama7B row.`
- expectation_status: `unspecified`
- evaluation_summary: `Hierarchical attention composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hierarchical_softmax_architecture__l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1.json: decision=two_pass_exact_selected; online_pass=False; online_error_bound_q16=655; lengths=[128, 4096, 131072]; distributions=['normal_std1', 'normal_std4', 'monotonic_ramp16']; llama7b_score_buffer={'bytes': 16777216, 'current_shared_sram_mib': 68, 'fits_current_shared_sram': True, 'mib': 16.0}; width_bounds={'exp_sum_bits': 33, 'exp_sum_bits_required': 33, 'max_block_count': 16384, 'max_context_tokens': 131072, 'max_exp_sum': 8589803520, 'max_weighted_numerator_magnitude': 1099494850560, 'merge_scale_bits': 24, 'weighted_numerator_bits': 41, 'weighted_numerator_signed_bits_required': 41}; next_step=Implement the two-pass global-max/score-replay datapath and retain online merge only as an approximate comparison.`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `hierarchical_composition_gate`
- proposal_outcome: `two_pass_exact_selected`
- comparison_summary: `Hierarchical attention composition evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hierarchical_softmax_architecture__l2_decoder_attention_hierarchical_softmax_architecture_llama7b_v1.json: decision=two_pass_exact_selected; online_pass=False; online_error_bound_q16=655; lengths=[128, 4096, 131072]; distributions=['normal_std1', 'normal_std4', 'monotonic_ramp16']; llama7b_score_buffer={'bytes': 16777216, 'current_shared_sram_mib': 68, 'fits_current_shared_sram': True, 'mib': 16.0}; width_bounds={'exp_sum_bits': 33, 'exp_sum_bits_required': 33, 'max_block_count': 16384, 'max_context_tokens': 131072, 'max_exp_sum': 8589803520, 'max_weighted_numerator_magnitude': 1099494850560, 'merge_scale_bits': 24, 'weighted_numerator_bits': 41, 'weighted_numerator_signed_bits_required': 41}; next_step=Implement the two-pass global-max/score-replay datapath and retain online merge only as an approximate comparison.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

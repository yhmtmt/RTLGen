## Summary
- item_id: `l2_decoder_attention_separated_cluster_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_separated_cluster_equivalence_llama7b_v1_run_ceb654dd3e3eb22c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_separated_cluster_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_separated_cluster_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_separated_cluster_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_separated_cluster_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_separated_cluster_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `6efe80945e1c3a2424a7f25fa532f5b2a3c7cd60`
- review_metadata_source_commit: `6efe80945e1c3a2424a7f25fa532f5b2a3c7cd60`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_separated_cluster_equivalence`
- comparison_role: `semantic_equivalence_gate`
- expected_direction: `prove_attention_separated_cluster_equivalence`
- expected_reason: `Physical evaluation is ineligible until exact QK, softmax, weighted-V, ordering, and backpressure behavior match the perf model.`
- expectation_status: `unspecified`
- evaluation_summary: `Separated attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_cluster_equivalence__l2_decoder_attention_separated_cluster_equivalence_llama7b_v1.json: decision=attention_separated_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_w16_exp_lut_div_b20; ratios=['1:1', '2:1', '4:1', '8:1', '4:2', '8:2']; command_count=8; scenarios=['always_ready', 'intermittent_consumer_stall', 'all_consumers_blocked_temporarily', 'result_backpressure']; gates={'exact_ready_valid_schedule': True, 'exact_score_rows': True, 'exact_softmax_weights': True, 'exact_weighted_value_vectors': True, 'loss_or_duplication': False}; remaining_abstractions=['the bounded 8x8 attention tile must be replicated and scheduled across the full Llama7B dimensions', 'PPA and toggle-based power for each producer-to-consumer ratio are not measured by this equivalence probe']; next_step=Measure Nangate45 PPA for 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 producer-to-consumer ratios.`

## Focused Comparison
- primary_question: `After exact perf/RTL equivalence, how do producer:consumer ratios 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 trade Nangate45 area, power, clock, peak score-row service, and burst buffering?`
- comparison_role: `semantic_equivalence_gate`
- proposal_outcome: `attention_separated_cluster_equivalence_pass`
- comparison_summary: `Separated attention perf/RTL equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_separated_cluster_equivalence__l2_decoder_attention_separated_cluster_equivalence_llama7b_v1.json: decision=attention_separated_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_w16_exp_lut_div_b20; ratios=['1:1', '2:1', '4:1', '8:1', '4:2', '8:2']; command_count=8; scenarios=['always_ready', 'intermittent_consumer_stall', 'all_consumers_blocked_temporarily', 'result_backpressure']; gates={'exact_ready_valid_schedule': True, 'exact_score_rows': True, 'exact_softmax_weights': True, 'exact_weighted_value_vectors': True, 'loss_or_duplication': False}; remaining_abstractions=['the bounded 8x8 attention tile must be replicated and scheduled across the full Llama7B dimensions', 'PPA and toggle-based power for each producer-to-consumer ratio are not measured by this equivalence probe']; next_step=Measure Nangate45 PPA for 1:1, 2:1, 4:1, 8:1, 4:2, and 8:2 producer-to-consumer ratios.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

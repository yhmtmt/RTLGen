## Summary
- item_id: `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1`
- run_key: `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1_run_70af86414c940825`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_softmax_frontier_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `2634eede3c91b2c85d339784ed630f7fecdfc514`
- review_metadata_source_commit: `2634eede3c91b2c85d339784ed630f7fecdfc514`

## Evaluation Mode
- evaluation_mode: `quality_equivalence_gate`
- abstraction_layer: `decoder_attention_softmax_pow2sum_quality`
- comparison_role: `softmax_replacement_quality_gate`
- expected_direction: `quality_gate_pow2sum`
- expected_reason: `Record whether pow2sum preserves Llama7B-shape top-1/retrieval/output quality before architecture promotion.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json: decision=mixed_precision_quality_blocked; best_quality_candidate=q8_k8_v6_a24_s8_w8_softmax_rtl_exact; best_quality_decision=mixed_precision_risky; best_low_cost_candidate=None; best_low_cost_decision=None; passing_candidate_count=0; borderline_candidate_count=0; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery.`

## Focused Comparison
- primary_question: `Is the softmax bottleneck better addressed by splitting the exact softmax datapath or by replacing exact sum division with a cheaper approximation?`
- comparison_role: `softmax_replacement_quality_gate`
- proposal_outcome: `mixed_precision_quality_blocked`
- comparison_summary: `Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1.json: decision=mixed_precision_quality_blocked; best_quality_candidate=q8_k8_v6_a24_s8_w8_softmax_rtl_exact; best_quality_decision=mixed_precision_risky; best_low_cost_candidate=None; best_low_cost_decision=None; passing_candidate_count=0; borderline_candidate_count=0; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=hold mixed-precision compute promotion and test safer precision or QAT/model-native recovery.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

## Summary
- item_id: `l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1`
- run_key: `l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1_run_17f8c31b94bbdc4a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0f76c959af3d547b55491546970268d88586e85c`
- review_metadata_source_commit: `98812adafb0c9fa81aaf526f38ed790ed84cdf52`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_score32_zero_tail_generation_quality`
- comparison_role: `two_pass_zero_tail_generation_quality`
- expected_direction: `qualify_zero_tail_two_pass_precision`
- expected_reason: `The earlier score32 quality pass clamps out-of-range LUT deltas to exp(-8) and cannot be transferred to the implemented zero-tail profile.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_zero_tail_two_pass_generation_quality__l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_zero_tail_two_pass; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.875; free_run_token_match_rate=0.890625; diverged_prompt_count=1; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0759302119170522; teacher_forced_mean_nll_delta=0.0021601149860883124; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.4479474380335404; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `two_pass_zero_tail_generation_quality`
- proposal_outcome: `mixed_int8_generation_quality_pass`
- comparison_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score32_zero_tail_two_pass_generation_quality__l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_zero_tail_two_pass; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.875; free_run_token_match_rate=0.890625; diverged_prompt_count=1; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0759302119170522; teacher_forced_mean_nll_delta=0.0021601149860883124; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.4479474380335404; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- resolver_retry_path: `true`
- submission_failure_count: `1`
- retry_request_count: `1`
- last_submission_failure: `work item l2_decoder_attention_score32_zero_tail_two_pass_generation_quality_llama7b_v1 is not eligible for submission: proposal already finalized with decision=promote`
- retry_request_id: `resume_3e32b2f009c2d882`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

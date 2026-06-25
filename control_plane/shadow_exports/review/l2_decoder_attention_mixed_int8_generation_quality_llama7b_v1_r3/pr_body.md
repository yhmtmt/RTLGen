## Summary
- item_id: `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3`
- run_key: `l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3_run_daa0e970350921ef`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e73b2f80d545f5236fa8c67cd1ca11006a8bea0e`
- review_metadata_source_commit: `e73b2f80d545f5236fa8c67cd1ca11006a8bea0e`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_generation_quality`
- comparison_role: `generation_quality`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_float; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.84375; diverged_prompt_count=2; mean_first_divergence_step=6.625; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0760980009300023; teacher_forced_mean_nll_delta=0.0023279039990386913; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44887183254036667; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`

## Focused Comparison
- primary_question: `Does the score32 mixed/int8 attention path preserve bounded greedy generation and teacher-forced reference-token likelihood on a 7B checkpoint?`
- comparison_role: `generation_quality`
- proposal_outcome: `mixed_int8_generation_quality_pass`
- comparison_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_generation_quality__l2_decoder_attention_mixed_int8_generation_quality_llama7b_v1_r3.json: decision=mixed_int8_generation_quality_pass; candidate_id=score32_float; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.84375; diverged_prompt_count=2; mean_first_divergence_step=6.625; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0760980009300023; teacher_forced_mean_nll_delta=0.0023279039990386913; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44887183254036667; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

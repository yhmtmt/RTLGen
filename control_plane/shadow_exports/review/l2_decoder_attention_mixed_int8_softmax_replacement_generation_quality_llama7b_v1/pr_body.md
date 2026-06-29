## Summary
- item_id: `l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1_run_c33510d19aaf6429`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c697832fc58789af79c407266536866bd03aa31f`
- review_metadata_source_commit: `c697832fc58789af79c407266536866bd03aa31f`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_softmax_replacement_generation_quality`
- comparison_role: `softmax_replacement_generation_quality`
- expected_direction: `choose_softmax_replacement_after_rtl_exact_failure`
- expected_reason: `RTL exact-divide failed the same generation-quality gate as reciprocal-LUT q16, so sweep replacement softmax shapes before more PPA runs.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_softmax_replacement_generation_quality__l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=qkv8_q24_pwl_recip_q24_bucket8; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.875; diverged_prompt_count=2; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0921800072287313; teacher_forced_mean_nll_delta=0.01840991029776741; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44199434749935546; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`

## Focused Comparison
- primary_question: `Which replacement score/softmax shape recovers bounded greedy generation and teacher-forced reference-token likelihood when score32/w16 RTL exact-divide softmax fails?`
- comparison_role: `softmax_replacement_generation_quality`
- proposal_outcome: `mixed_int8_generation_quality_pass`
- comparison_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_softmax_replacement_generation_quality__l2_decoder_attention_mixed_int8_softmax_replacement_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_pass; candidate_id=qkv8_q24_pwl_recip_q24_bucket8; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.75; free_run_token_match_rate=0.875; diverged_prompt_count=2; mean_first_divergence_step=7.0; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=1.0921800072287313; teacher_forced_mean_nll_delta=0.01840991029776741; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.44199434749935546; next_step=Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

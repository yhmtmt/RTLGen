## Summary
- item_id: `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2`
- run_key: `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2_run_28d4fdd536b2164b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `23463c027a33c181540252eeefeffc5756d6c3a7`
- review_metadata_source_commit: `23463c027a33c181540252eeefeffc5756d6c3a7`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality`
- comparison_role: `score24_w16_rtl_exact_generation_quality`
- expected_direction: `direct_score24_w16_quality_gate`
- expected_reason: `Rerun after PR #1085 fixed hard-coded score32 wording in the generation-quality report; metrics should match v1 but artifacts must correctly identify score24/w16.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score24 w16 rtl exact mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.`

## Focused Comparison
- primary_question: `Does the measured score24/w16 RTL exact-divide softmax profile preserve bounded greedy generation and teacher-forced reference-token likelihood on a 7B checkpoint?`
- comparison_role: `score24_w16_rtl_exact_generation_quality`
- proposal_outcome: `mixed_int8_generation_quality_hold`
- comparison_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score24 w16 rtl exact mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `Command '['git', '-C', '/tmp/rtlgen-master-1085', 'worktree', 'add', '-b', 'eval/l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_r2/local-rescue-20260630t1310z', '/tmp/rtlgen-submissions/repo', 'refs/r...`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

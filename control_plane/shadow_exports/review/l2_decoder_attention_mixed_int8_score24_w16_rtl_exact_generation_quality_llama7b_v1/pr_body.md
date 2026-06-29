## Summary
- item_id: `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1_run_fc00ad658cae8fc8`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `2422334f7e275ccc49334522d978700361598aaa`
- review_metadata_source_commit: `2422334f7e275ccc49334522d978700361598aaa`

## Evaluation Mode
- evaluation_mode: `quality_gate`
- abstraction_layer: `decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality`
- comparison_role: `score24_w16_rtl_exact_generation_quality`
- expected_direction: `direct_score24_w16_quality_gate`
- expected_reason: `If score24/w16 RTL exact-divide passes, use the measured lower-area score24/w16 recost as the active quality-backed frontier. If it fails, keep the recost as physical evidence but plan recovery through higher precision, a different softmax model, or QAT.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score32 mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.`

## Focused Comparison
- primary_question: `Does the measured score24/w16 RTL exact-divide softmax profile preserve bounded greedy generation and teacher-forced reference-token likelihood on a 7B checkpoint?`
- comparison_role: `score24_w16_rtl_exact_generation_quality`
- proposal_outcome: `mixed_int8_generation_quality_hold`
- comparison_summary: `Decoder mixed/int8 generation quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality__l2_decoder_attention_mixed_int8_score24_w16_rtl_exact_generation_quality_llama7b_v1.json: decision=mixed_int8_generation_quality_hold; candidate_id=score24_w16_rtl_exact; prompt_count=8; generation_steps=8; free_run_exact_match_rate=0.0; free_run_token_match_rate=0.078125; diverged_prompt_count=8; mean_first_divergence_step=0.5; teacher_forced_mean_reference_nll=1.073770096930964; teacher_forced_mean_candidate_nll=2.6074809896126507; teacher_forced_mean_nll_delta=1.5337108926816854; teacher_forced_reference_token_prob_mean=0.4479845997119758; teacher_forced_candidate_reference_token_prob_mean=0.25191303969855044; next_step=Hold this score32 mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

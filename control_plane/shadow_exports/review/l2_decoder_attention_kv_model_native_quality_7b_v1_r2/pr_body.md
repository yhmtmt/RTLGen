## Summary
- item_id: `l2_decoder_attention_kv_model_native_quality_7b_v1_r2`
- run_key: `l2_decoder_attention_kv_model_native_quality_7b_v1_r2_run_115d2c5cc7ceec50`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_model_native_quality_7b_v1_r2/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_model_native_quality_7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_model_native_quality_7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_model_native_quality_7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `25029453e1bd386b4a8f2fc17bde6bd01d727149`
- review_metadata_source_commit: `62dce9666f6d0120264e3bfbd2d76a72cb7b6743`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_model_native_quality_7b`
- comparison_role: `precision_gate`
- expected_direction: `iterate`
- expected_reason: `v1 was killed with exit_code=-9; r2 uses bfloat16 and smaller prompt/step defaults to produce a bounded 7B native precision signal.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality_7b__l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json: decision=native_checkpoint_kv4_promising; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; kv4_kv_bits=4; kv4_kv_granularity=tensor; kv4_top1_match_rate=1.0; kv4_topk_contains_rate=1.0; kv4_mean_logit_cosine=0.9978199414249704; kv4_mean_probability_kl=0.01678496644161117; kv4_max_abs_logit_delta_max=2.3125; next_step=Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation.`

## Focused Comparison
- primary_question: `Does teacher-forced decode on a real 7B-class checkpoint preserve next-token rankings when past_key_values are quantized to KV8 or KV4?`
- comparison_role: `precision_gate`
- proposal_outcome: `native_checkpoint_kv4_promising`
- comparison_summary: `Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality_7b__l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json: decision=native_checkpoint_kv4_promising; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; kv4_kv_bits=4; kv4_kv_granularity=tensor; kv4_top1_match_rate=1.0; kv4_topk_contains_rate=1.0; kv4_mean_logit_cosine=0.9978199414249704; kv4_mean_probability_kl=0.01678496644161117; kv4_max_abs_logit_delta_max=2.3125; next_step=Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_model_native_quality_7b_v1_r2 is not eligible for submission: run l2_decoder_attention_kv_model_native_quality_7b_v1_r2_run_115d2c5cc7ceec50 has no validator-compatible metrics rows to export`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

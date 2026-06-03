## Summary
- item_id: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- run_key: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2_run_ff3db632b8d9c8c8`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1454629818ddaffb32375c31115845dd85390350`
- review_metadata_source_commit: `b89aca61bcc67a5b1a4b04b65c22fdb82ffbe083`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_attention_kv_physical_hbm_compute_sensitivity`
- comparison_role: `ranking`
- expected_direction: `quantify_compute_memory_boundary`
- expected_reason: `This pass should show whether increasing compute beyond the current measured local baseline matters once SRAM capacity, HBM service, and local/global NoC bounds dominate the Llama7B 131k attention schedule.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `What focused comparison directly tests this proposal?`
- comparison_role: `ranking`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

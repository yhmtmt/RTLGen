## Summary
- item_id: `l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1`
- run_key: `l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1_run_040b331fce39fb82`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f251105bedd542800001e68a205e6fb0910163cb`
- review_metadata_source_commit: `f251105bedd542800001e68a205e6fb0910163cb`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_physical_hbm_quality_backed`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If KV8 still leaves the 131k point HBM-bound, continue HBM/SRAM scheduling work; if KV8 clears the HBM wall, move to integration breakdown. KV4 remains a separate QAT/fine-tuning track.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_quality_backed__l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Under the physical HBM model, how much of the long-context llama7b_proxy bottleneck remains when the ranked choices are restricted to quality-backed native-GQA KV16 and KV8?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_quality_backed__l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/622`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

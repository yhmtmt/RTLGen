## Summary
- item_id: `l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2`
- run_key: `l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2_run_819568598c09ad78`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0bf76729d525e08aab8b8428ba2c4bb272c48aa5`
- review_metadata_source_commit: `0bf76729d525e08aab8b8428ba2c4bb272c48aa5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_physical_hbm_quality_backed_7b`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Consumes the r2 bounded 7B native quality gate so physical HBM reranking does not depend on the failed v1 artifact.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_quality_backed_7b__l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Under the physical HBM model, does the conservative native-GQA KV16/KV8 frontier remain the deployable Llama7B point when the quality evidence is taken from a 7B-class checkpoint?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_quality_backed_7b__l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_kv_physical_hbm_quality_backed_7b_llama7b_v1_r2 is not eligible for submission: missing developer_loop proposal linkage`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

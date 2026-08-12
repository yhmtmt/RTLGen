## Summary
- item_id: `l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1`
- run_key: `l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1_run_ad6e7c8adcd71d63`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `34cdb1ff66afc838d081156877c7dc2c00a3c076`
- review_metadata_source_commit: `844c86ab1107409ec97518b7896aab5d66a40df9`

## Evaluation Mode
- evaluation_mode: `equivalence`
- abstraction_layer: `decoder_attention_exact_partial_c1_workload_correspondence`
- comparison_role: `workload_correspondence_prerequisite`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_exact_partial_c1_workload_correspondence__l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Do deterministic schedule counters and exact values match bounded real RTL for every divider width at 10 ns / 12 ns, and are the full-window service deltas affine before projection to 5462 windows/head and 32 heads/layer?`
- comparison_role: `workload_correspondence_prerequisite`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_exact_partial_c1_workload_correspondence__l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- resolver_retry_path: `true`
- submission_failure_count: `1`
- retry_request_count: `1`
- last_submission_failure: `expected output not found for suffix /best_point.json: l2_decoder_attention_exact_partial_c1_workload_correspondence_llama7b_v1_r1`
- retry_request_id: `resume_db9185fd617f9ef0`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

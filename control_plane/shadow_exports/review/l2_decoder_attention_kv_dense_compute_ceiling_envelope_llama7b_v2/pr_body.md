## Summary
- item_id: `l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2`
- run_key: `l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2_run_b77ee0ffedd30350`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8d24df3d504c9c423f955974e05d419249da6a43`
- review_metadata_source_commit: `8d24df3d504c9c423f955974e05d419249da6a43`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_compute_ceiling_envelope`
- comparison_role: `frontier_synthesis`
- expected_direction: `update_compute_frontier_with_dense_measurement`
- expected_reason: `The job should show which die and logic budgets become feasible when the dense 8x8 tile replaces nm64_flat as measured best compute density.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the registered dense GEMM tile density make the Llama7B 131072 MAC/cycle HBM-bound floor physically plausible under the current die-size and logic-fraction envelope?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

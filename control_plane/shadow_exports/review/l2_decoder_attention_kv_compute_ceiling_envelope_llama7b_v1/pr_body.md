## Summary
- item_id: `l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1`
- run_key: `l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1_run_5be3a6be7c9c996c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_compute_ceiling_envelope_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `4f777beadc88002831f92432887be2a398ed1e64`
- review_metadata_source_commit: `4f777beadc88002831f92432887be2a398ed1e64`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_compute_ceiling_envelope`
- comparison_role: `frontier_synthesis`
- expected_direction: `bound_compute_frontier`
- expected_reason: `The job should identify whether measured, optimistic, or aggressive 45nm compute-density assumptions can reach the HBM-bound floor.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which die size, logic fraction, and compute-density envelope can plausibly reach the 131072 MAC/cycle HBM-bound floor?`
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

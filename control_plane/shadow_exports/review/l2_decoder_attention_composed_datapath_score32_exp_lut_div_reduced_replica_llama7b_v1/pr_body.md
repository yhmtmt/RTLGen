## Summary
- item_id: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1_run_ff57a9e29c709725`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `711696b8304bc02537b6e7aa59757eb42f55d078`
- review_metadata_source_commit: `e7a3eac95ad1ead9c24d5facdbbd90390069a305`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `score32_exp_lut_div_reduced_replica_recost`
- expected_direction: `recost_exp_lut_div_composed_datapath_after_quality_gate_and_l1_ppa`
- expected_reason: `Recost the exp-LUT composed datapath only after the L1 exp-LUT divider gate is available and the L2 quality gate passes; do not treat this as quality-backed until the quality decision is affirmative.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `What Llama7B latency/area/energy point is defined by the measured score32 exp-LUT divider composed datapath when bound by the same reduced-replica constraints?`
- comparison_role: `score32_exp_lut_div_reduced_replica_recost`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1 is not eligible for submission: work item l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_llama7b_v1 is not ready ...`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

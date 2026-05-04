## Summary
- item_id: `l2_decoder_gpt2_logit_rank_bypass_v1_r2`
- run_key: `l2_decoder_gpt2_logit_rank_bypass_v1_r2_run_9aa31b07a5ca98aa`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `12/12 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_gpt2_logit_rank_bypass_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_gpt2_logit_rank_bypass_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_gpt2_logit_rank_bypass_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_gpt2_logit_rank_bypass_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_gpt2_logit_rank_bypass_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `778f05d3a849ad902da9b8031318d6aa5ef50167`
- review_metadata_source_commit: `778f05d3a849ad902da9b8031318d6aa5ef50167`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_gpt2_logit_rank_bypass`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Rerun should keep the exact-safe rank-bypass quality gate and record measured logit_rank_datapath PPA with argmax k=1 and top-k k=4 rows.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does a GPT-2 prompt-stress candidate that bypasses softmax and ranks raw logits match the exact-softmax next-token and top-k decisions?`
- comparison_role: `ranking`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

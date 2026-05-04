## Summary
- item_id: `l2_decoder_gpt2_logit_rank_bypass_v1`
- run_key: `l2_decoder_gpt2_logit_rank_bypass_v1_run_3133c3273b1669b0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `12/12 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_gpt2_logit_rank_bypass_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_gpt2_logit_rank_bypass_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_gpt2_logit_rank_bypass_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_gpt2_logit_rank_bypass_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_gpt2_logit_rank_bypass_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `cbeb2d85c78953fddec2c01204ce59393757b876`
- review_metadata_source_commit: `cbeb2d85c78953fddec2c01204ce59393757b876`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_gpt2_logit_rank_bypass`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Confirm raw-logit ranking can remove softmax normalization for GPT-2 greedy/top-k serving while keeping sampling out of scope.`
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

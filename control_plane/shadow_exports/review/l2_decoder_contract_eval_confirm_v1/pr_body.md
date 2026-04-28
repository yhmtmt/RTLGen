## Summary
- item_id: `l2_decoder_contract_eval_confirm_v1`
- run_key: `l2_decoder_contract_eval_confirm_v1_run_532701d69527b741`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `9/9 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_contract_eval_confirm_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_contract_eval_confirm_v1.json`

## Developer Context
- proposal_id: `prop_l2_llm_attention_tail_v1`
- proposal_path: `docs/proposals/prop_l2_llm_attention_tail_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_llm_attention_tail_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0d6f8ec8e5aadfad4629d74120992c9bcd49bd60`
- review_metadata_source_commit: `0d6f8ec8e5aadfad4629d74120992c9bcd49bd60`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Confirmation job records decoder contract and quality-gate health, not architecture improvement.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which current architecture point best supports LLM attention-tail scheduling evidence?`
- comparison_role: `ranking`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

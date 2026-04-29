## Summary
- item_id: `l2_llm_practical_decoder_proxy_v1`
- run_key: `l2_llm_practical_decoder_proxy_v1_run_1ca7cdd943f79644`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_llm_practical_decoder_proxy_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_llm_practical_decoder_proxy_v1.json`

## Developer Context
- proposal_id: `prop_l2_llm_practical_decoder_proxy_v1`
- proposal_path: `docs/proposals/prop_l2_llm_practical_decoder_proxy_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_llm_practical_decoder_proxy_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `1c7e32188a70d5336a2f0dd85cbc37f7caa8fcc9`
- review_metadata_source_commit: `1c7e32188a70d5336a2f0dd85cbc37f7caa8fcc9`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `layer2`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Practical proxy evidence should decide whether to pursue scheduler/KV-context work, continue toward dataset-backed decoder execution, or reconsider softmax datapath proposals.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the first practical decoder-style proxy expose scheduler, softmax, or KV-context pressure that was absent from the attention-tail stress ladder?`
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

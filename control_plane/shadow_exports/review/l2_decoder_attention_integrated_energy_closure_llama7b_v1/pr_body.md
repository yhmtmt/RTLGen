## Summary
- item_id: `l2_decoder_attention_integrated_energy_closure_llama7b_v1`
- run_key: `l2_decoder_attention_integrated_energy_closure_llama7b_v1_run_bf7b9ecd51d37eec`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_integrated_energy_closure_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_integrated_energy_closure_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_integrated_energy_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_integrated_energy_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_integrated_energy_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `874a6fc4692f0cf65916b7bf41c2270ddb8ac130`
- review_metadata_source_commit: `9c54c5e820e9df8071686c9a2ff74cbb394555b7`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_integrated_energy_closure`
- comparison_role: `frontier_closure`
- expected_direction: `record_integrated_energy_closure_frontier`
- expected_reason: `Record measured-plus-parameterized integrated energy for the selected Llama7B attention frontier and expose remaining energy abstractions.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `After adding explicit integrated-energy accounting to the merged abstraction-closure baseline, which Llama7B 131k attention frontier point remains dominant and which measured or parameterized energy terms still need closure?`
- comparison_role: `frontier_closure`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/966`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

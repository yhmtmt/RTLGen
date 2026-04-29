## Summary
- item_id: `l2_decoder_distribution_robustness_v1`
- run_key: `l2_decoder_distribution_robustness_v1_run_8cc46e0843306e63`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `10/10 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_distribution_robustness_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_distribution_robustness_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_distribution_robustness_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_distribution_robustness_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_distribution_robustness_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c9674dafe98bf8a1199a8cbcb5dc06311422f09b`
- review_metadata_source_commit: `c9674dafe98bf8a1199a8cbcb5dc06311422f09b`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `decoder_distribution_robustness`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `The map should show whether the q/fp approximation cliffs persist across broader prompt/logit entropy and top-1 margin regimes before any narrow approximation parameter tuning.`
- expectation_status: `unspecified`
- evaluation_summary: `Broad ranking evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Across a broader rough prompt-regime set, which integer and fp-like decoder probability-path approximations preserve next-token and top-k rank as entropy and top-1/top-2 margins vary?`
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

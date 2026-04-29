## Summary
- item_id: `l2_decoder_survivor_cost_proxy_v1`
- run_key: `l2_decoder_survivor_cost_proxy_v1_run_b90ca2a069fb29be`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_survivor_cost_proxy_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_survivor_cost_proxy_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_survivor_cost_proxy_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_survivor_cost_proxy_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_survivor_cost_proxy_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d1a0addc723413f289cf7a92c7a580b9f1e585df`
- review_metadata_source_commit: `d1a0addc723413f289cf7a92c7a580b9f1e585df`

## Evaluation Mode
- evaluation_mode: `cost_proxy`
- abstraction_layer: `decoder_survivor_cost_proxy`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Rank exact-safe PWL and probability paths by explicit cost assumptions before committing to a hardware-cost candidate.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Among exact-safe decoder survivor rows, which approximation family has the lowest relative softmax/probability-path implementation cost under a stated proxy model?`
- comparison_role: `ranking`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

## Summary
- item_id: `l2_prop_l2_mapper_memory_aware_split_v1_latency`
- run_key: `l2_prop_l2_mapper_memory_aware_split_v1_latency_run_3727f48d1b54c3c2`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_memory_aware_split_v1_latency/evaluated.json`
- metrics_rows_count: `12`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_memory_aware_split_v1_latency.json`

## Developer Context
- proposal_id: `prop_l2_mapper_memory_aware_split_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_memory_aware_split_v1`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_memory_aware_split_v1` plus `docs/developer_agent_review.md`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

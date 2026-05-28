## Summary
- item_id: `l1_decoder_attention_kv_reducer_tree_frontier_v1`
- run_key: `l1_decoder_attention_kv_reducer_tree_frontier_v1_run_cb30f0208d7f1095`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_kv_reducer_tree_frontier_v1/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_kv_reducer_tree_frontier_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_kv_reducer_tree_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_kv_reducer_tree_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_kv_reducer_tree_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `2c159e39a100ccc443d0529e51ab0c8304bd912d`
- review_metadata_source_commit: `9714b78ea0334d50d87673e99065ff596d7d9886`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `attention_kv_reducer_tree`
- evaluation_summary: `No status=ok Layer 1 rows were produced; non-ok metrics rows are recorded as explicit boundary evidence.`

## Focused Comparison
- proposal_outcome: `boundary_no_feasible_points`
- comparison_summary: `All current Layer 1 metrics rows are non-ok; this is accepted as frontier boundary evidence, not a promotable design point.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

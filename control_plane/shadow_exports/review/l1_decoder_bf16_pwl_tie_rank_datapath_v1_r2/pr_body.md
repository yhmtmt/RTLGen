## Summary
- item_id: `l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2`
- run_key: `l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2_run_cb92c6e2f2dc394c`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json`

## Developer Context
- proposal_id: `prop_l1_decoder_bf16_pwl_tie_rank_datapath_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_bf16_pwl_tie_rank_datapath_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_bf16_pwl_tie_rank_datapath_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `f20792b7148976c2e8fbaa6b86e0964447a5eab1`
- review_metadata_source_commit: `f20792b7148976c2e8fbaa6b86e0964447a5eab1`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `circuit_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

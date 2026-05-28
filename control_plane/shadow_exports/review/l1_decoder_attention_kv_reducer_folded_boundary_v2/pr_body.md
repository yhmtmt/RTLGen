## Summary
- item_id: `l1_decoder_attention_kv_reducer_folded_boundary_v2`
- run_key: `l1_decoder_attention_kv_reducer_folded_boundary_v2_run_691135f111e9d719`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_kv_reducer_folded_boundary_v2/evaluated.json`
- metrics_rows_count: `36`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_kv_reducer_folded_boundary_v2.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_kv_reducer_folded_boundary_v2`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_kv_reducer_folded_boundary_v2`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_kv_reducer_folded_boundary_v2` plus `docs/developer_agent_review.md`
- execution_source_commit: `d3095707fd1eae291a944b1f215ebe9882c5efe2`
- review_metadata_source_commit: `d3095707fd1eae291a944b1f215ebe9882c5efe2`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `attention_kv_reducer_folded`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

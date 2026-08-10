## Summary
- item_id: `l1_decoder_attention_exact_partial_temporal_finalizer_bounded_12ns_physical_v1_r1`
- run_key: `l1_decoder_attention_exact_partial_temporal_finalizer_bounded_12ns_physical_v1_r1_run_3b8f840b56dfab56`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `18/18 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_exact_partial_temporal_finalizer_bounded_12ns_physical_v1_r1/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_exact_partial_temporal_finalizer_bounded_12ns_physical_v1_r1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_exact_partial_temporal_finalizer_bounded_physical_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_exact_partial_temporal_finalizer_bounded_physical_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_exact_partial_temporal_finalizer_bounded_physical_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `e27482f94d94ba45de684f7e9a3d5c5727161dd9`
- review_metadata_source_commit: `c7cd8eebb24a8f0e24db93f131683b14208b3b66`

## Evaluation Mode
- evaluation_mode: `physical_calibration`
- abstraction_layer: `decoder_attention_exact_partial_temporal_finalizer`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

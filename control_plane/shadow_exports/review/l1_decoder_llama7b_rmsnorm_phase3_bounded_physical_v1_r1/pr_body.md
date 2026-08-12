## Summary
- item_id: `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1`
- run_key: `l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1_run_ac8b6daeb1245602`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1_r1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_llama7b_rmsnorm_phase3_bounded_physical_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `aa752025f0742fe4496ef0940eea3a2ea96a488b`
- review_metadata_source_commit: `a9c5a0c5afd8e673dc1d423c172271ca1dcb8499`

## Evaluation Mode
- evaluation_mode: `physical_calibration`
- abstraction_layer: `llama7b_rmsnorm_phase3`
- evaluation_summary: `No status=ok Layer 1 rows were produced; non-ok metrics rows are recorded as explicit boundary evidence.`

## Focused Comparison
- proposal_outcome: `boundary_no_feasible_points`
- comparison_summary: `All current Layer 1 metrics rows are non-ok; this is accepted as frontier boundary evidence, not a promotable design point.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

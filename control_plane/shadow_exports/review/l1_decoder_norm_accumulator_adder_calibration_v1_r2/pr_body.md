## Summary
- item_id: `l1_decoder_norm_accumulator_adder_calibration_v1_r2`
- run_key: `l1_decoder_norm_accumulator_adder_calibration_v1_r2_run_468c5ccfebeb29c6`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_norm_accumulator_adder_calibration_v1_r2/evaluated.json`
- metrics_rows_count: `88`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_norm_accumulator_adder_calibration_v1_r2.json`

## Developer Context
- proposal_id: `prop_l1_decoder_normalization_arithmetic_calibration_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_normalization_arithmetic_calibration_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_normalization_arithmetic_calibration_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ea6095808f683c26979575365f9a5c4249470a05`
- review_metadata_source_commit: `ea6095808f683c26979575365f9a5c4249470a05`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `circuit_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

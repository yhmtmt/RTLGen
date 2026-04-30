## Summary
- item_id: `l1_decoder_bf16_recip_norm_datapath_v1_r2`
- run_key: `l1_decoder_bf16_recip_norm_datapath_v1_r2_run_78aed7d4bbe695a5`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_bf16_recip_norm_datapath_v1_r2/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json`

## Developer Context
- proposal_id: `prop_l1_decoder_bf16_recip_norm_datapath_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_bf16_recip_norm_datapath_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_bf16_recip_norm_datapath_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `604d30b4165ef8b79b16997782979e7313735615`
- review_metadata_source_commit: `f2f3aa70565d3183e0c597e7c7a03c56edb77713`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `circuit_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Submission Recovery
- submission_failure_count: `2`
- retry_request_count: `0`
- last_submission_failure: `work item l1_decoder_bf16_recip_norm_datapath_v1_r2 is not eligible for submission: work item l1_decoder_bf16_recip_norm_datapath_v1_r2 is not eligible for submission: proposal already finalized with decision=promote`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

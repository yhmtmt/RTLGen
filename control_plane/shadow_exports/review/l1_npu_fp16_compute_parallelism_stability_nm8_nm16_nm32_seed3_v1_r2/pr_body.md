## Summary
- item_id: `l1_npu_fp16_compute_parallelism_stability_nm8_nm16_nm32_seed3_v1_r2`
- run_key: `l1_npu_fp16_compute_parallelism_stability_nm8_nm16_nm32_seed3_v1_r2_run_34c3b2955b6b98b0`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `2/3 seed trials succeeded; 1 trial failures recorded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_fp16_compute_parallelism_stability_nm8_nm16_nm32_seed3_v1_r2/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_fp16_compute_parallelism_stability_nm8_nm16_nm32_seed3_v1_r2.json`

## Developer Context
- proposal_id: `prop_l1_npu_fp16_compute_parallelism_stability_v1`
- proposal_path: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_stability_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_stability_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8676df60746526fc9b52620f4eaf0e6e85d0845e`
- review_metadata_source_commit: `8676df60746526fc9b52620f4eaf0e6e85d0845e`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_compute_parallelism_stability`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

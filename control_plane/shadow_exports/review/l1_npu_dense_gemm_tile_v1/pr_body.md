## Summary
- item_id: `l1_npu_dense_gemm_tile_v1`
- run_key: `l1_npu_dense_gemm_tile_v1_run_c4388265f4a94642`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `9/9 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_dense_gemm_tile_v1/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_dense_gemm_tile_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_dense_gemm_tile_v1`
- proposal_path: `docs/proposals/prop_l1_npu_dense_gemm_tile_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_npu_dense_gemm_tile_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `bd380995d64fdf1bf7f63034c7de280f700085ac`
- review_metadata_source_commit: `bd380995d64fdf1bf7f63034c7de280f700085ac`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `architecture_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

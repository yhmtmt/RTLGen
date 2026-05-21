## Summary
- item_id: `l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1`
- run_key: `l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1_run_a7f297dce0578d92`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `13/13 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1/evaluated.json`
- metrics_rows_count: `40`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_fp16_compute_parallelism_gate_count_audit_v1`
- proposal_path: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_gate_count_audit_v1`
- reviewer_first_read: `docs/proposals/prop_l1_npu_fp16_compute_parallelism_gate_count_audit_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `99286a0eb503f85857df5fc31db64dc33f0ab243`
- review_metadata_source_commit: `99286a0eb503f85857df5fc31db64dc33f0ab243`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `npu_compute_parallelism_gate_count`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

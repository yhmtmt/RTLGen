## Summary
- item_id: `l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r14`
- run_key: `l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r14_run_e5669ec1aac9d7a7`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r14/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_prop_l1_npu_nm1_sigmoid_vec_enable_v1_r14.json`

## Developer Context
- proposal_id: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- proposal_path: `docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1/proposal.json`
- reviewer_first_read: `docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1/proposal.json` plus `docs/developer_agent_review.md`

## Evaluation Mode
- evaluation_mode: `synth_prefilter`
- evaluation_summary: `Synth-stage prefilter passed at `1_1_yosys_canonicalize`; no physical metrics are recorded yet.`

## Checklist
- [ ] Commit only lightweight metrics and regenerated runs/index.csv
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

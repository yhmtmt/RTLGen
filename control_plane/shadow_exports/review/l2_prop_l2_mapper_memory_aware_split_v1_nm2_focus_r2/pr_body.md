## Summary
- item_id: `l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2`
- run_key: `l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2_run_222d50984d386595`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2.json`

## Developer Context
- proposal_id: `prop_l2_mapper_memory_aware_split_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_memory_aware_split_v1`
- reviewer_first_read: `docs/developer_loop/prop_l2_mapper_memory_aware_split_v1` plus `docs/developer_agent_review.md`

## Focused Comparison
- primary_question: `Does the bounded mapper change materially improve nm2 on the existing softmaxcmp hardware?`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_softmax_tile_fusion_v1_20260316051355`
- latency_delta fp16_nm2_softmax_r4/flat_nomacro: `0.000928` -> `0.000621` ms
- energy_delta fp16_nm2_softmax_r4/flat_nomacro: `1.7546067199999999e-07` -> `1.17414954e-07` mJ
- latency_delta fp16_nm2_softmax_r4/hier_macro: `0.000928` -> `0.000621` ms
- energy_delta fp16_nm2_softmax_r4/hier_macro: `1.8455878400000002e-07` -> `1.23503238e-07` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

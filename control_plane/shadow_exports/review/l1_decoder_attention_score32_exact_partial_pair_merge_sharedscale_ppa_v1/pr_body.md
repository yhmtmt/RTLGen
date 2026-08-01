## Summary
- item_id: `l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1`
- run_key: `l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1_run_b17933308cb1b8c4`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `23dcda4fc523c0d467e71debdf45136fce6eaede`
- review_metadata_source_commit: `23dcda4fc523c0d467e71debdf45136fce6eaede`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `architecture_block`
- evaluation_summary: `No timing-feasible Layer 1 rows were produced; completed flows that miss their declared clock period are retained as explicit timing-boundary evidence.`

## Focused Comparison
- proposal_outcome: `boundary_no_feasible_points`
- comparison_summary: `All completed physical rows miss their declared clock period; retain them as timing-boundary evidence and do not promote a feasible design point.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

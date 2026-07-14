## Summary
- item_id: `l1_decoder_attention_operational_dense_tile_ppa_v1`
- run_key: `l1_decoder_attention_operational_dense_tile_ppa_v1_run_cb0b9acc6498034e`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_operational_dense_tile_ppa_v1/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_operational_dense_tile_ppa_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `cda8e38dd420e1ef41109b76a0b3710d359771ac`
- review_metadata_source_commit: `cda8e38dd420e1ef41109b76a0b3710d359771ac`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_operational_dense_tile`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

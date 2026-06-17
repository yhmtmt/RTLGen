## Summary
- item_id: `l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1`
- run_key: `l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1_run_10530f798d2176cb`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1/evaluated.json`
- metrics_rows_count: `12`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `276f12403c2e08e8cd9b5e891a8b1fb151b33de7`
- review_metadata_source_commit: `276f12403c2e08e8cd9b5e891a8b1fb151b33de7`

## Evaluation Mode
- evaluation_mode: `frontier_closure`
- abstraction_layer: `architecture_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

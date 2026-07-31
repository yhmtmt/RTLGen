## Summary
- item_id: `l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1`
- run_key: `l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1_run_2db447e07253665a`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `18/18 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1/evaluated.json`
- metrics_rows_count: `8`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_score32_exact_root_finalizer_lane_ppa_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `86d8d9aa30ad93a7e0e7b84fc2bdd894175862f0`
- review_metadata_source_commit: `86d8d9aa30ad93a7e0e7b84fc2bdd894175862f0`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `architecture_block`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

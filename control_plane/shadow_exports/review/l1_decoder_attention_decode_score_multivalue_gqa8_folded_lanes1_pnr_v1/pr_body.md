## Summary
- item_id: `l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes1_pnr_v1`
- run_key: `l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes1_pnr_v1_run_8857771f82730cc7`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes1_pnr_v1/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_decode_score_multivalue_gqa8_folded_lanes1_pnr_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_gqa8_group_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f63fd55c1360dcc9b072e672c8ccc0ff2234ac6b`
- review_metadata_source_commit: `837af0d8fb6f19c815602208a5f85bda698a84b8`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_decode_score_multivalue_gqa_folded_lane`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

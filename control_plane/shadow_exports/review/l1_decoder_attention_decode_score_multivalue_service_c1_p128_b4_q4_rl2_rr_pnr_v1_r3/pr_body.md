## Summary
- item_id: `l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r3`
- run_key: `l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r3_run_5bf089fc8ab688a2`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r3/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_pnr_v1_r3.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_decode_score_multivalue_service_pnr_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `712fa5a05c388e944ace6003191dceeb995a4edc`
- review_metadata_source_commit: `712fa5a05c388e944ace6003191dceeb995a4edc`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_decode_score_multivalue_service`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

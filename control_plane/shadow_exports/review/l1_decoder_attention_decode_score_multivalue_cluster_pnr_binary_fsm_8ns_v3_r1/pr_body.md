## Summary
- item_id: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3_r1`
- run_key: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3_r1_run_809db01f928e6545`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3_r1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_decode_score_multivalue_cluster_pnr_binary_fsm_8ns_v3_r1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `57c6dd86b35cb227a001c0cc7e6327d2ca8c91c2`
- review_metadata_source_commit: `57c6dd86b35cb227a001c0cc7e6327d2ca8c91c2`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_decode_score_multivalue_cluster`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

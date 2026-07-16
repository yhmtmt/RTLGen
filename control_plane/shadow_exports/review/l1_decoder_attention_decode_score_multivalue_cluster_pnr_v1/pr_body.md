## Summary
- item_id: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1`
- run_key: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1_run_6999bb7c1b6aba41`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `fail`
- summary: `command run_block_sweep failed (canceled)`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `40fd671e19b79660e28ecf99ab07f38043e0e937`
- review_metadata_source_commit: `1a6f5c814d9212c312248cf2e4efe96490e58e4b`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_decode_score_multivalue_cluster`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Focused Comparison
- proposal_outcome: `partial_sweep_measured_points`
- comparison_summary: `The run terminated after capturing status=ok physical rows. Retain only those rows as measured evidence; the sweep is incomplete and unmeasured points must not be inferred as feasible.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

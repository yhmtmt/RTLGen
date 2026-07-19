## Summary
- item_id: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2`
- run_key: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2_run_78eb87f44c4c61c8`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2/evaluated.json`
- metrics_rows_count: `1`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_decode_score_multivalue_cluster_pnr_8ns_v2.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `9a857c5cb5deb84ae5487d1b0c37500833bd7e1a`
- review_metadata_source_commit: `35e8575df0e8de61fc483f1c277a9881602703df`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_decode_score_multivalue_cluster`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Submission Recovery
- submission_failure_count: `0`
- retry_request_count: `0`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/1364`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

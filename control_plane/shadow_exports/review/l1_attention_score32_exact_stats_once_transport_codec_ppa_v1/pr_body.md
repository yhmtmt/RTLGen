## Summary
- item_id: `l1_attention_score32_exact_stats_once_transport_codec_ppa_v1`
- run_key: `l1_attention_score32_exact_stats_once_transport_codec_ppa_v1_run_124cac9c70f2e42a`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_attention_score32_exact_stats_once_transport_codec_ppa_v1/evaluated.json`
- metrics_rows_count: `18`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_attention_score32_exact_stats_once_transport_codec_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_attention_score32_exact_stats_once_transport_codec_ppa_v1`
- proposal_path: `docs/proposals/prop_l1_attention_score32_exact_stats_once_transport_codec_ppa_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_attention_score32_exact_stats_once_transport_codec_ppa_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `3db4f8efc2b7ead6257b09d4d1df9e070f8bb6b1`
- review_metadata_source_commit: `a39136fc11ccc0558e9d390d5dc62b91f2cff19e`

## Evaluation Mode
- evaluation_mode: `ppa`
- abstraction_layer: `architecture_block`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

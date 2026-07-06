## Summary
- item_id: `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_ppa_v1`
- run_key: `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_ppa_v1_run_8267373119f80f74`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `15/15 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_ppa_v1/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_parallelism_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `f7218288fb8ef0057559f6f9cbbf91b81cf045fc`
- review_metadata_source_commit: `f7218288fb8ef0057559f6f9cbbf91b81cf045fc`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_dual_stream_composed_datapath`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

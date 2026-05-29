## Summary
- item_id: `l1_decoder_attention_kv_reducer_folded_producer_coupled_v1`
- run_key: `l1_decoder_attention_kv_reducer_folded_producer_coupled_v1_run_119e9ef63707579d`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_kv_reducer_folded_producer_coupled_v1/evaluated.json`
- metrics_rows_count: `16`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_kv_reducer_folded_producer_coupled_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_kv_reducer_folded_producer_coupled_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_kv_reducer_folded_producer_coupled_v1`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_kv_reducer_folded_producer_coupled_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `ab5e84aae179c0a4da2d86e5553a8cf25a0cfb4b`
- review_metadata_source_commit: `ab5e84aae179c0a4da2d86e5553a8cf25a0cfb4b`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `attention_kv_reducer_folded`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

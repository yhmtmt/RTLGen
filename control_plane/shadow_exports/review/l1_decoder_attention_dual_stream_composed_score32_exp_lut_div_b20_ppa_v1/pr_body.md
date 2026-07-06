## Summary
- item_id: `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1`
- run_key: `l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1_run_1d69e46c4c21a245`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `heartbeat_error=(psycopg.OperationalError) connection failed: connection to server at "192.168.128.8", port 5432 failed: server closed the connection unexpectedly
	This probably means the server terminated abnormally
	before or while processing the request.
(Background on this error at: https://sqlalche.me/e/20/e3q8)`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1/evaluated.json`
- metrics_rows_count: `2`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_score32_exp_lut_div_b20_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `432be4180b3abc5f0257109038e3b7e3ecc02a14`
- review_metadata_source_commit: `432be4180b3abc5f0257109038e3b7e3ecc02a14`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_dual_stream_composed_datapath`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

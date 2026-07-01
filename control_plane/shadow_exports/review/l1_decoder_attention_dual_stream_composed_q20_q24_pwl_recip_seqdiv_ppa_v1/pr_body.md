## Summary
- item_id: `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1`
- run_key: `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1_run_d51696a71badc45f`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1/evaluated.json`
- metrics_rows_count: `4`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `78a9417eebf722c68ebe6ace381856125452e8aa`
- review_metadata_source_commit: `78a9417eebf722c68ebe6ace381856125452e8aa`

## Evaluation Mode
- evaluation_mode: `measurement_only`
- abstraction_layer: `decoder_attention_dual_stream_composed_datapath`
- evaluation_summary: `No status=ok Layer 1 rows were produced; non-ok metrics rows are recorded as explicit boundary evidence.`

## Focused Comparison
- proposal_outcome: `boundary_no_feasible_points`
- comparison_summary: `All current Layer 1 metrics rows are non-ok; this is accepted as frontier boundary evidence, not a promotable design point.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

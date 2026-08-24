## Summary
- item_id: `l1_attention_shared_sram_k_round_scheduler_b17_w17_ppa_v1`
- run_key: `l1_attention_shared_sram_k_round_scheduler_b17_w17_ppa_v1_run_1e3a07564a774435`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_attention_shared_sram_k_round_scheduler_b17_w17_ppa_v1/evaluated.json`
- metrics_rows_count: `6`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_attention_shared_sram_k_round_scheduler_b17_w17_ppa_v1.json`

## Developer Context
- proposal_id: `prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1`
- proposal_path: `docs/proposals/prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_attention_shared_sram_k_round_scheduler_ppa_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8886192007592abc57a8e1928d8c3122462b6922`
- review_metadata_source_commit: `25a32bd6e2c28259eb2a35935ad806a562b512da`

## Evaluation Mode
- evaluation_mode: `physical_calibration`
- abstraction_layer: `decoder_attention_shared_sram_k_prefetch_scheduler`
- evaluation_summary: `Physical metrics recorded from a completed, timing-feasible Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

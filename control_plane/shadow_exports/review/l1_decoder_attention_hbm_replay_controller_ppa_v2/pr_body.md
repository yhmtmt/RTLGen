## Summary
- item_id: `l1_decoder_attention_hbm_replay_controller_ppa_v2`
- run_key: `l1_decoder_attention_hbm_replay_controller_ppa_v2_run_09cd3d8c1647ed2c`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `14/14 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_hbm_replay_controller_ppa_v2/evaluated.json`
- metrics_rows_count: `9`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_hbm_replay_controller_ppa_v2.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_hbm_replay_controller_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_hbm_replay_controller_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_hbm_replay_controller_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `de5a546bfa7d0f7f34c9bd4872f5e7e689b67924`
- review_metadata_source_commit: `de5a546bfa7d0f7f34c9bd4872f5e7e689b67924`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_hbm_replay_controller`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing

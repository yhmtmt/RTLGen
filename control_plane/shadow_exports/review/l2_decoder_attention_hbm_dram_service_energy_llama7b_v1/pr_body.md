## Summary
- item_id: `l2_decoder_attention_hbm_dram_service_energy_llama7b_v1`
- run_key: `l2_decoder_attention_hbm_dram_service_energy_llama7b_v1_run_4984fd7af97fdb93`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_hbm_dram_service_energy_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_hbm_dram_service_energy_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_hbm_dram_service_energy_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_hbm_dram_service_energy_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_hbm_dram_service_energy_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c9169759f666977ab33a5bd461efe947db3775d8`
- review_metadata_source_commit: `c9169759f666977ab33a5bd461efe947db3775d8`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_hbm_dram_service_energy`
- comparison_role: `frontier_closure`
- expected_direction: `record_hbm_dram_service_energy_frontier`
- expected_reason: `Determine whether the HBM-energy-sensitive frontier remains stable under explicit DRAM command/service accounting.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does a lightweight HBM/DRAM command-service energy model preserve or move the Llama7B latency-best, energy-best, and balanced frontier points?`
- comparison_role: `frontier_closure`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

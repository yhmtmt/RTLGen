## Summary
- item_id: `l2_decoder_logit_rank_streaming_sram_nangate45_v1`
- run_key: `l2_decoder_logit_rank_streaming_sram_nangate45_v1_run_d17e26943f2c7a2d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_logit_rank_streaming_sram_nangate45_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_logit_rank_streaming_sram_nangate45_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_logit_rank_streaming_sram_nangate45_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_logit_rank_streaming_sram_nangate45_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_logit_rank_streaming_sram_nangate45_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `79856b13dbbc93b3de1ed2198baa3303e72aac74`
- review_metadata_source_commit: `79856b13dbbc93b3de1ed2198baa3303e72aac74`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_logit_rank_streaming_overlap`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Confirm the decoder streaming memory frontier with Nangate45 SRAM metrics while NoC remains a planning term.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Does the memory-aware decoder streaming frontier change when SRAM energy comes from the Nangate45 minimal_v0_2_draft SRAM artifact instead of a planning default?`
- comparison_role: `ranking`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

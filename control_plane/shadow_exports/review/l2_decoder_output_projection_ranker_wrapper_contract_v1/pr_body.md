## Summary
- item_id: `l2_decoder_output_projection_ranker_wrapper_contract_v1`
- run_key: `l2_decoder_output_projection_ranker_wrapper_contract_v1_run_780850e900b0662c`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_ranker_wrapper_contract_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_ranker_wrapper_contract_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_ranker_wrapper_contract_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_ranker_wrapper_contract_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_ranker_wrapper_contract_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `79cae818b82aedf850438211a69dbb1f505e39af`
- review_metadata_source_commit: `79cae818b82aedf850438211a69dbb1f505e39af`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_ranker_wrapper_contract`
- comparison_role: `producer_ranker_service`
- expected_direction: `iterate`
- expected_reason: `If the representative serial, r64 rank-tree, and banked r128 contract cases pass, implement the final wrapper mux/control RTL and then run a physical wrapper sweep.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Do representative serial, rank-tree r64, and banked rank-tree r128 cases satisfy the promoted policy contract before implementing final wrapper mux/control RTL?`
- comparison_role: `producer_ranker_service`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

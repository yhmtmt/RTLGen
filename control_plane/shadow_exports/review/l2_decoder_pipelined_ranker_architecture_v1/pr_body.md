## Summary
- item_id: `l2_decoder_pipelined_ranker_architecture_v1`
- run_key: `l2_decoder_pipelined_ranker_architecture_v1_run_47f2ca337c6ef5c7`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `8/8 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_pipelined_ranker_architecture_v1/evaluated.json`
- metrics_rows_count: `27`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_pipelined_ranker_architecture_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_pipelined_ranker_architecture_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_pipelined_ranker_architecture_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_pipelined_ranker_architecture_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `549e1b18b7b4dc464912b656a9cf669035163af8`
- review_metadata_source_commit: `549e1b18b7b4dc464912b656a9cf669035163af8`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_pipelined_ranker_architecture`
- comparison_role: `ranker_pipeline_architecture`
- expected_direction: `iterate`
- expected_reason: `Find the best r64 segmented/pipelined ranker anchor before r128 or producer-coupled scaling.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Which segmented r64/k1 ranker parallelism point gives the best first timing/PPA tradeoff after adding register cuts?`
- comparison_role: `ranker_pipeline_architecture`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

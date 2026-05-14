## Summary
- item_id: `l2_decoder_output_projection_producer_pnr_nm16_v1`
- run_key: `l2_decoder_output_projection_producer_pnr_nm16_v1_run_77bd8da6bd65c8ee`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_pnr_nm16_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_pnr_nm16_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_pnr_nm16_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_pnr_nm16_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_pnr_nm16_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `bb6fbafe99dcfc2659b95f8cc5a4e5dc766b8cb2`
- review_metadata_source_commit: `bb6fbafe99dcfc2659b95f8cc5a4e5dc766b8cb2`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_pnr_feasibility`
- comparison_role: `producer_pnr_feasibility`
- expected_direction: `iterate`
- expected_reason: `The result should report whether nm16 completes bounded physical implementation or identify the first placement-stage blocker for a floorplan or hierarchy follow-up.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_pnr_feasibility__l2_decoder_output_projection_producer_pnr_nm16_v1.json: decision=producer_physical_boundary_not_reached; recommended_next_step=Use the largest completed physical point for near-frontier extrapolation or extend cautiously.`

## Focused Comparison
- primary_question: `Can the post-scoreboard nm16 decoder output-projection producer complete the bounded Nangate45 3_3_place_gp physical target?`
- comparison_role: `producer_pnr_feasibility`
- proposal_outcome: `producer_physical_boundary_not_reached`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_pnr_feasibility__l2_decoder_output_projection_producer_pnr_nm16_v1.json: decision=producer_physical_boundary_not_reached; recommended_next_step=Use the largest completed physical point for near-frontier extrapolation or extend cautiously.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

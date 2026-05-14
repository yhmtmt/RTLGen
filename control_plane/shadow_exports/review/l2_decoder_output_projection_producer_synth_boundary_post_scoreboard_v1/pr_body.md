## Summary
- item_id: `l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1`
- run_key: `l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1_run_fb2dd13fd528464f`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `74e781a0eee1cac95b1fbc415c39fa41d90de360`
- review_metadata_source_commit: `74e781a0eee1cac95b1fbc415c39fa41d90de360`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_synth_boundary`
- comparison_role: `producer_synth_boundary`
- expected_direction: `iterate`
- expected_reason: `The result should identify whether nm2 now completes after removing the wide event_state vector, and if not, preserve the exact new failure signature for the next small RTL change.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_synth_boundary__l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1.json: decision=producer_synth_boundary_not_reached; recommended_next_step=Extend the probe to the next producer scale before launching full PnR.`

## Focused Comparison
- primary_question: `After the bounded EVENT scoreboard fix, what is the largest decoder output-projection producer module count that completes bounded synth-only compilation?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `producer_synth_boundary_not_reached`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_synth_boundary__l2_decoder_output_projection_producer_synth_boundary_post_scoreboard_v1.json: decision=producer_synth_boundary_not_reached; recommended_next_step=Extend the probe to the next producer scale before launching full PnR.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

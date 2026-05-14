## Summary
- item_id: `l2_decoder_output_projection_producer_event_scoreboard_v1`
- run_key: `l2_decoder_output_projection_producer_event_scoreboard_v1_run_70e5e989fe18345e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_event_scoreboard_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_event_scoreboard_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_event_scoreboard_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_event_scoreboard_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_event_scoreboard_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `dbad5522be1193b3abffbfe96a37d1df59e5cf6f`
- review_metadata_source_commit: `dbad5522be1193b3abffbfe96a37d1df59e5cf6f`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_softmax_event_ablation`
- comparison_role: `producer_synth_boundary`
- expected_direction: `promote`
- expected_reason: `EVENT_WAIT-only, full EVENT, and SOFTMAX/EVENT guard variants should move from timeout to bounded synth result once the wide dynamic event_state vector is removed.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_softmax_event_ablation__l2_decoder_output_projection_producer_event_scoreboard_v1.json: decision=softmax_event_guard_synth_ok_under_bound; recommended_next_step=Use the guard metrics as an updated synthesis boundary before changing RTL.`

## Focused Comparison
- primary_question: `Does a bounded EVENT scoreboard make the prior EVENT_WAIT-only, full EVENT, and SOFTMAX/EVENT guard variants synthesize under the nm2 bounded probe?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `softmax_event_guard_synth_ok_under_bound`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_softmax_event_ablation__l2_decoder_output_projection_producer_event_scoreboard_v1.json: decision=softmax_event_guard_synth_ok_under_bound; recommended_next_step=Use the guard metrics as an updated synthesis boundary before changing RTL.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

## Summary
- item_id: `l2_decoder_output_projection_producer_event_wait_staged_v1`
- run_key: `l2_decoder_output_projection_producer_event_wait_staged_v1_run_ad3b7b36639d2b28`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_event_wait_staged_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_event_wait_staged_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_event_wait_staged_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_event_wait_staged_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_event_wait_staged_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `349a499fda759dc08b5a8e1e92a40d2826530d4c`
- review_metadata_source_commit: `349a499fda759dc08b5a8e1e92a40d2826530d4c`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_softmax_event_ablation`
- comparison_role: `producer_synth_boundary`
- expected_direction: `promote`
- expected_reason: `EVENT_WAIT-only and full EVENT variants should move from timeout to bounded synth result after staging the descriptor-indexed event_state access.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_softmax_event_ablation__l2_decoder_output_projection_producer_event_wait_staged_v1.json: decision=softmax_event_subpath_culprit_bracketed; recommended_next_step=Inspect the first non-OK SOFTMAX/EVENT subpath and replace the failing expression with staged decode or preserved hierarchy.`

## Focused Comparison
- primary_question: `Does the staged EVENT_WAIT RTL make the prior EVENT_WAIT and combined SOFTMAX/EVENT CQ variants synthesize under the bounded nm2 probe?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `softmax_event_subpath_culprit_bracketed`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_softmax_event_ablation__l2_decoder_output_projection_producer_event_wait_staged_v1.json: decision=softmax_event_subpath_culprit_bracketed; recommended_next_step=Inspect the first non-OK SOFTMAX/EVENT subpath and replace the failing expression with staged decode or preserved hierarchy.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

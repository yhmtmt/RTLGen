## Summary
- item_id: `l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1`
- run_key: `l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1_run_4f50f469336d0111`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `24e591a06f0c3c0941df3f975e907e294ebd6b08`
- review_metadata_source_commit: `24e591a06f0c3c0941df3f975e907e294ebd6b08`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_synth_boundary`
- comparison_role: `producer_synth_boundary`
- expected_direction: `iterate`
- expected_reason: `The result should report whether nm8 and nm16 complete synth-only compilation or record the first nonviable module count for the next hierarchy or macro-hardening change.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_synth_boundary__l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1.json: decision=producer_synth_boundary_not_reached; recommended_next_step=Extend the probe to the next producer scale before launching full PnR.`

## Focused Comparison
- primary_question: `Does the post-scoreboard full producer wrapper remain synth-feasible at nm8 and nm16 under the same bounded synth-only target?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `producer_synth_boundary_not_reached`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_synth_boundary__l2_decoder_output_projection_producer_synth_boundary_nm8_nm16_v1.json: decision=producer_synth_boundary_not_reached; recommended_next_step=Extend the probe to the next producer scale before launching full PnR.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

## Summary
- item_id: `l2_decoder_output_projection_producer_isolated_synth_scale_v1`
- run_key: `l2_decoder_output_projection_producer_isolated_synth_scale_v1_run_b0cc1fabebae7e87`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_isolated_synth_scale_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_isolated_synth_scale_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_isolated_synth_scale_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_isolated_synth_scale_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_isolated_synth_scale_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `38c4b6c4661c15bd5190ef89e9c5323245db7502`
- review_metadata_source_commit: `38c4b6c4661c15bd5190ef89e9c5323245db7502`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_isolated_synth`
- comparison_role: `producer_synth_boundary`
- expected_direction: `iterate`
- expected_reason: `Extend isolated gemm_compute_array synth boundary from nm2 to nm4 before retrying whole npu_top or full PnR.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_isolated_synth__l2_decoder_output_projection_producer_isolated_synth_scale_v1.json: decision=producer_synth_boundary_not_reached; recommended_next_step=Extend the probe to the next producer scale before launching full PnR.`

## Focused Comparison
- primary_question: `Can the isolated generated gemm_compute_array producer submodule complete synth-only compilation for nm1 through nm4 within the evaluator budget?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `producer_synth_boundary_not_reached`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_isolated_synth__l2_decoder_output_projection_producer_isolated_synth_scale_v1.json: decision=producer_synth_boundary_not_reached; recommended_next_step=Extend the probe to the next producer scale before launching full PnR.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

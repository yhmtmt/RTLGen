## Summary
- item_id: `l2_decoder_output_projection_producer_synth_boundary_v1_r2`
- run_key: `l2_decoder_output_projection_producer_synth_boundary_v1_r2_run_92590c3cc129cd54`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_synth_boundary_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_synth_boundary_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_synth_boundary_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_synth_boundary_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c9a4757707c6e4c51f047c2eed2466ab717ecb3b`
- review_metadata_source_commit: `c9a4757707c6e4c51f047c2eed2466ab717ecb3b`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_synth_boundary`
- comparison_role: `producer_synth_boundary`
- expected_direction: `iterate`
- expected_reason: `Bound synth runtime explosion before retrying full producer PnR after preparing rtlgen.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_synth_boundary__l2_decoder_output_projection_producer_synth_boundary_v1_r2.json: decision=producer_synth_boundary_recorded; recommended_next_step=Use the largest completed synth point for near-frontier extrapolation and split or macro-harden larger producers before retrying full physical implementation.`

## Focused Comparison
- primary_question: `At what output-projection producer module count does synth-only compilation stop completing within the bounded evaluator budget?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `producer_synth_boundary_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_synth_boundary__l2_decoder_output_projection_producer_synth_boundary_v1_r2.json: decision=producer_synth_boundary_recorded; recommended_next_step=Use the largest completed synth point for near-frontier extrapolation and split or macro-harden larger producers before retrying full physical implementation.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

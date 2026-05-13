## Summary
- item_id: `l2_decoder_output_projection_producer_top_ablation_v1`
- run_key: `l2_decoder_output_projection_producer_top_ablation_v1_run_8ac08310c39057ea`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_top_ablation_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_top_ablation_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_top_ablation_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_top_ablation_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_top_ablation_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `db05f3ba9e0c4d79a72f99201fc79c0de4bdefa2`
- review_metadata_source_commit: `db05f3ba9e0c4d79a72f99201fc79c0de4bdefa2`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_top_ablation`
- comparison_role: `producer_synth_boundary`
- expected_direction: `iterate`
- expected_reason: `Identify which nm2 npu_top integration feature causes whole-top synth to become nonviable while isolated gemm_compute_array remains viable.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_top_ablation__l2_decoder_output_projection_producer_top_ablation_v1.json: decision=producer_top_culprit_bracketed; recommended_next_step=Compare the last passing ablation against the full reference to isolate the added top-level feature.`

## Focused Comparison
- primary_question: `Which top-level npu_top feature first causes the nm2 producer synth-only run to become nonviable?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `producer_top_culprit_bracketed`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_top_ablation__l2_decoder_output_projection_producer_top_ablation_v1.json: decision=producer_top_culprit_bracketed; recommended_next_step=Compare the last passing ablation against the full reference to isolate the added top-level feature.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

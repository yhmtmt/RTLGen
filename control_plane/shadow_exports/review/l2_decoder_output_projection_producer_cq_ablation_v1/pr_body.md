## Summary
- item_id: `l2_decoder_output_projection_producer_cq_ablation_v1`
- run_key: `l2_decoder_output_projection_producer_cq_ablation_v1_run_b3a5f111cbb32bbe`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_output_projection_producer_cq_ablation_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_output_projection_producer_cq_ablation_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_output_projection_producer_cq_ablation_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_output_projection_producer_cq_ablation_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_output_projection_producer_cq_ablation_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `886574dd25ad57d2bca73db0cb9a279f3b3e365d`
- review_metadata_source_commit: `886574dd25ad57d2bca73db0cb9a279f3b3e365d`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_output_projection_producer_cq_ablation`
- comparison_role: `producer_synth_boundary`
- expected_direction: `iterate`
- expected_reason: `The output should identify the first CQ subpath that becomes nonviable, or show that each individual subpath is viable and a pairwise interaction probe is required.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_cq_ablation__l2_decoder_output_projection_producer_cq_ablation_v1.json: decision=cq_subpath_culprit_bracketed; recommended_next_step=Compare the first non-OK CQ subpath against the preceding OK subpath and stage or preserve hierarchy around that decode/issue expression.`

## Focused Comparison
- primary_question: `Which command-queue subpath first changes the nm2 producer top from synth-viable to synth-nonviable?`
- comparison_role: `producer_synth_boundary`
- proposal_outcome: `cq_subpath_culprit_bracketed`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_output_projection_producer_cq_ablation__l2_decoder_output_projection_producer_cq_ablation_v1.json: decision=cq_subpath_culprit_bracketed; recommended_next_step=Compare the first non-OK CQ subpath against the preceding OK subpath and stage or preserve hierarchy around that decode/issue expression.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

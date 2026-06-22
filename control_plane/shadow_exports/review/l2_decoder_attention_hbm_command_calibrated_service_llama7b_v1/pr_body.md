## Summary
- item_id: `l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1`
- run_key: `l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1_run_9e58828040c0e65a`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `fe4ca975710eb00fcc06a99579ded3d59c58d58b`
- review_metadata_source_commit: `fe4ca975710eb00fcc06a99579ded3d59c58d58b`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_hbm_command_calibrated_service`
- comparison_role: `frontier_closure`
- expected_direction: `record_hbm_command_calibrated_service`
- expected_reason: `Scale the command-class HBM service model to source-backed aggregate HBM energy and test row-hit sensitivity before final Llama7B energy ranking.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_command_calibrated_service__l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json: decision=hbm_command_calibrated_service_preserves_frontier; recommended_next_step=Use the command-calibrated HBM service result to decide whether to invest next in cycle-accurate HBM controller/current modeling or in direct compute-energy measurement.`

## Focused Comparison
- primary_question: `Does source-scaled command-class HBM service accounting preserve the Llama7B energy-best family under row-hit sensitivity?`
- comparison_role: `frontier_closure`
- proposal_outcome: `hbm_command_calibrated_service_preserves_frontier`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_command_calibrated_service__l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json: decision=hbm_command_calibrated_service_preserves_frontier; recommended_next_step=Use the command-calibrated HBM service result to decide whether to invest next in cycle-accurate HBM controller/current modeling or in direct compute-energy measurement.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

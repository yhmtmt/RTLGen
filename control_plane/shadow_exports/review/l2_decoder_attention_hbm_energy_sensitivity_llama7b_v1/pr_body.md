## Summary
- item_id: `l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1`
- run_key: `l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1_run_24790f1180d34773`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `76e4dad9e738e331f924df8f2e45ffa2a6a01088`
- review_metadata_source_commit: `76e4dad9e738e331f924df8f2e45ffa2a6a01088`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_hbm_energy_sensitivity`
- comparison_role: `frontier_closure`
- expected_direction: `record_hbm_energy_sensitivity_frontier`
- expected_reason: `Expose sensitivity to the dominant HBM pJ/byte energy term before claiming an energy-optimal Llama7B attention point.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_sensitivity__l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1.json: decision=hbm_energy_sensitivity_changes_energy_optimum; recommended_next_step=close HBM/DRAM energy and service modeling before claiming an energy-optimal Llama7B point.`

## Focused Comparison
- primary_question: `Does the selected Llama7B 131k attention frontier remain best when HBM energy per byte is swept, or does the energy optimum move to a larger-memory point?`
- comparison_role: `frontier_closure`
- proposal_outcome: `hbm_energy_sensitivity_changes_energy_optimum`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_sensitivity__l2_decoder_attention_hbm_energy_sensitivity_llama7b_v1.json: decision=hbm_energy_sensitivity_changes_energy_optimum; recommended_next_step=close HBM/DRAM energy and service modeling before claiming an energy-optimal Llama7B point.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

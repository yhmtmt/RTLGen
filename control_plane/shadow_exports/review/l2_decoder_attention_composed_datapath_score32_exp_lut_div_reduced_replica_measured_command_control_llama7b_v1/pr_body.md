## Summary
- item_id: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1_run_8fb1e4f1e66b1b08`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_measured_command_control_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_measured_command_control_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_measured_command_control_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ac37f5b6eae677d83c9a872ae99df446d8596096`
- review_metadata_source_commit: `ac37f5b6eae677d83c9a872ae99df446d8596096`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `score32_exp_lut_div_measured_command_control_recost`
- expected_direction: `charge_measured_command_control_to_exp_lut_recost`
- expected_reason: `This replaces a purely idealized scheduler/control area-power assumption with measured central command-dispatch PPA before final frontier promotion.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `How much do measured central command-dispatch/control area, power, and clock move the score32 exp-LUT divider reduced-replica Llama7B point?`
- comparison_role: `score32_exp_lut_div_measured_command_control_recost`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

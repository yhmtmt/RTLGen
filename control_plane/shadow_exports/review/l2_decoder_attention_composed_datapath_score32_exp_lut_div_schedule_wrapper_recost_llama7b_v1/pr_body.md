## Summary
- item_id: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1_run_66358cf5ca04ecf7`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ea8827725629262304c2eff8fc5a1adf12ef91d7`
- review_metadata_source_commit: `ea8827725629262304c2eff8fc5a1adf12ef91d7`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `score32_exp_lut_schedule_wrapper_recost`
- expected_direction: `replace_modeled_schedule_control_with_measured_wrapper`
- expected_reason: `Replace modeled schedule/control composition with measured c2/c4 schedule-wrapper PPA in the Llama7B area-fit recost.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `Does measured bounded schedule-wrapper PPA change the score32 exp-LUT Llama7B frontier versus the prior parallelism recost?`
- comparison_role: `score32_exp_lut_schedule_wrapper_recost`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

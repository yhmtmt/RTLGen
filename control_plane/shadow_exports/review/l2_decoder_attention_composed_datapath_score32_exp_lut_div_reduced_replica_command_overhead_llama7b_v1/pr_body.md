## Summary
- item_id: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1_run_81bd160d265ea41e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `7/7 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_command_overhead_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_command_overhead_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_command_overhead_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `6dc402784774ddde5693a61cecd7169d894ab20d`
- review_metadata_source_commit: `6dc402784774ddde5693a61cecd7169d894ab20d`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `score32_exp_lut_div_command_overhead_recost`
- expected_direction: `bound_command_overhead_on_exp_lut_composed_datapath`
- expected_reason: `Record whether command-dispatch overhead materially changes the exp-LUT reduced-replica latency ranking; keep the result dependency-gated and non-promotable if the exp-LUT quality gate fails.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`

## Focused Comparison
- primary_question: `How much does nonzero per-tile and per-wave command-dispatch overhead move the score32 exp-LUT divider reduced-replica Llama7B latency point?`
- comparison_role: `score32_exp_lut_div_command_overhead_recost`
- proposal_outcome: `dual_stream_feasible`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing

# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_measured_command_control_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1`
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1_run_8fb1e4f1e66b1b08`
- source commit: `ac37f5b6eae677d83c9a872ae99df446d8596096`
- review: PR #1194

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `dual_stream_feasible`
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.
- next_action: inspect follow-on work after l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_measured_command_control_llama7b_v1

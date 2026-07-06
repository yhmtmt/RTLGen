# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_command_overhead_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1`
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1_run_81bd160d265ea41e`
- source commit: `6dc402784774ddde5693a61cecd7169d894ab20d`
- review: PR #1189

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `dual_stream_feasible`
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.
- next_action: inspect follow-on work after l2_decoder_attention_composed_datapath_score32_exp_lut_div_reduced_replica_command_overhead_llama7b_v1

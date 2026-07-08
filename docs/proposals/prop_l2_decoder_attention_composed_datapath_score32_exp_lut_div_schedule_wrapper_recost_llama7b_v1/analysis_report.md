# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`

## Evaluations Consumed
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`
- `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1_run_66358cf5ca04ecf7`
- source commit: `ea8827725629262304c2eff8fc5a1adf12ef91d7`
- review: PR #1218

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `dual_stream_feasible`
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json: decision=dual_stream_feasible; recommended_next_step=promote dual-stream schedule into a measured RTL/PPA wrapper.
- next_action: inspect follow-on work after l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1

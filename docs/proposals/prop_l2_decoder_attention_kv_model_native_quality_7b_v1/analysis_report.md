# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_model_native_quality_7b_v1`
- `candidate_id`: `l2_decoder_attention_kv_model_native_quality_7b_v1_r2`

## Evaluations Consumed
- `l2_decoder_attention_kv_model_native_quality_7b_v1_r2`
- `l2_decoder_attention_kv_model_native_quality_7b_v1_r2_run_115d2c5cc7ceec50`
- source commit: `25029453e1bd386b4a8f2fc17bde6bd01d727149`
- review: PR #954

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `native_checkpoint_kv4_promising`
- summary: Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality_7b__l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json: decision=native_checkpoint_kv4_promising; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; kv4_kv_bits=4; kv4_kv_granularity=tensor; kv4_top1_match_rate=1.0; kv4_topk_contains_rate=1.0; kv4_mean_logit_cosine=0.9978199414249704; kv4_mean_probability_kl=0.01678496644161117; kv4_max_abs_logit_delta_max=2.3125; next_step=Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality_7b__l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json: decision=native_checkpoint_kv4_promising; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; kv4_kv_bits=4; kv4_kv_granularity=tensor; kv4_top1_match_rate=1.0; kv4_topk_contains_rate=1.0; kv4_mean_logit_cosine=0.9978199414249704; kv4_mean_probability_kl=0.01678496644161117; kv4_max_abs_logit_delta_max=2.3125; next_step=Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder native-checkpoint KV quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality_7b__l2_decoder_attention_kv_model_native_quality_7b_v1_r2.json: decision=native_checkpoint_kv4_promising; model_id=mistralai/Mistral-7B-v0.1; attention_heads=32; kv_heads=8; gqa_group_size=4.0; dtype=bfloat16; kv4_kv_bits=4; kv4_kv_granularity=tensor; kv4_top1_match_rate=1.0; kv4_topk_contains_rate=1.0; kv4_mean_logit_cosine=0.9978199414249704; kv4_mean_probability_kl=0.01678496644161117; kv4_max_abs_logit_delta_max=2.3125; next_step=Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation.
- next_action: inspect follow-on work after l2_decoder_attention_kv_model_native_quality_7b_v1_r2

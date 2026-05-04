# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_gpt2_prompt_stress_v1`
- `candidate_id`: `l2_decoder_gpt2_prompt_stress_v1`

## Evaluations Consumed
- `l2_decoder_gpt2_prompt_stress_v1`
- `l2_decoder_gpt2_prompt_stress_v1_run_afa2563567a387f6`
- source commit: `3b247257c2074fb6650da86032a2feb7305e176f`
- review: PR #384

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `tie_break_recovery_sufficient`
- summary: Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json: decision=tie_break_recovery_sufficient; exact_safe_after_recovery=True; recovered_count=2; regression_count=0; recommended_next_step=Treat bf16/PWL as the immediate low-cost frontier and follow with a hardware-friendly score-tie ranking check before full QAT infrastructure.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json: decision=tie_break_recovery_sufficient; exact_safe_after_recovery=True; recovered_count=2; regression_count=0; recommended_next_step=Treat bf16/PWL as the immediate low-cost frontier and follow with a hardware-friendly score-tie ranking check before full QAT infrastructure.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json: decision=tie_break_recovery_sufficient; exact_safe_after_recovery=True; recovered_count=2; regression_count=0; recommended_next_step=Treat bf16/PWL as the immediate low-cost frontier and follow with a hardware-friendly score-tie ranking check before full QAT infrastructure.
- next_action: inspect follow-on work after l2_decoder_gpt2_prompt_stress_v1

# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_gpt2_quality_v1`
- `candidate_id`: `l2_decoder_gpt2_quality_v1`

## Evaluations Consumed
- `l2_decoder_gpt2_quality_v1`
- `l2_decoder_gpt2_quality_v1_run_8ba8c7fe3ad8cf83`
- source commit: `ef58e573b0ddd2059e4d37eaacf40059676e0d8a`
- review: PR #382

## Baseline Comparison
- baseline_ref: `None`
- baseline_item_id: `None`
- outcome: `baseline_exact_safe`
- summary: Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_trained_v1/decoder_gpt2_quality__l2_decoder_gpt2_quality_v1.json: decision=baseline_exact_safe; exact_safe_after_recovery=True; recovered_count=0; regression_count=0; recommended_next_step=Treat bf16/PWL as exact-safe on this screen without relying on the logit tie-breaker; keep the tie-break row as a ranking-stability guard for broader prompts or larger checkpoints.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_trained_v1/decoder_gpt2_quality__l2_decoder_gpt2_quality_v1.json: decision=baseline_exact_safe; exact_safe_after_recovery=True; recovered_count=0; regression_count=0; recommended_next_step=Treat bf16/PWL as exact-safe on this screen without relying on the logit tie-breaker; keep the tie-break row as a ranking-stability guard for broader prompts or larger checkpoints.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_trained_v1/decoder_gpt2_quality__l2_decoder_gpt2_quality_v1.json: decision=baseline_exact_safe; exact_safe_after_recovery=True; recovered_count=0; regression_count=0; recommended_next_step=Treat bf16/PWL as exact-safe on this screen without relying on the logit tie-breaker; keep the tie-break row as a ranking-stability guard for broader prompts or larger checkpoints.
- next_action: inspect follow-on work after l2_decoder_gpt2_quality_v1

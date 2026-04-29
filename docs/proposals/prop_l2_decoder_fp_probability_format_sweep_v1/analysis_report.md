# Analysis Report

## Status

- `proposal_id`: `prop_l2_decoder_fp_probability_format_sweep_v1`
- `candidate_id`: `l2_decoder_fp_probability_format_sweep_v1`
- status: pending evaluator run

## Expected Artifact

- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_fp_probability_format_sweep_v1.json`

## Review Focus

- Compare fp-like final probability formats against the fixed unsigned q8
  probability collapse observed in `l2_decoder_probability_sensitivity_v1`.
- Inspect whether fp8 formats preserve rank/top-k for the pinned tiny decoder.
- Treat all results as distribution-dependent and rough.

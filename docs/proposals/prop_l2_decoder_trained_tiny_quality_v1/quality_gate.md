# Quality Gate

The evaluator must generate fresh reference and candidate manifests from
`runs/datasets/llm_decoder_eval_trained_tiny_v1/manifest.json`, validate the
decoder contract, compare exact reference versus the default candidate, then
run the built-in `decoder_bf16_pwl_scale_probe_v1` grid.

The final summary must report baseline misses, recovered sample ids, regression
sample ids, and the exact-safe status of the bf16/PWL logit tie-break row. If
the tie-break row is not exact-safe, the next job should diagnose trained-logit
margin failures before any larger checkpoint import.

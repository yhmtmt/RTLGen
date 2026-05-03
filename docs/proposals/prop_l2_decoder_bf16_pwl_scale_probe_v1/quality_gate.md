# Quality Gate

The evaluator must generate fresh reference and candidate manifests from
`manifest_scale_proxy_v1.json`, then run the built-in
`decoder_bf16_pwl_scale_probe_v1` grid. The final summary must report baseline
misses, recovered sample ids, regression sample ids, and the exact-safe status
of the logit tie-break row.

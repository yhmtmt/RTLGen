# Softmax reciprocal-LUT int8-compute feasibility

This proposal checks whether the current softmax reciprocal-LUT Llama7B frontier can recover the
`dual_mac` schedule after replacing the dense compute area model with measured signed-int8 GEMM PPA.

The exact-Q8/V16 physical check left the current physically valid point at `split_mac`
(`2042.378179 us`) because `dual_mac` exceeded the compute area budget. A dry-run with measured
int8 dense compute reported `dual_stream_feasible` at `1575.373891 us`, but that result needs to be
recorded through the control-plane job path.

The generator uses the checked-in mixed-precision quality JSON for the estimator and separately records
the finalized reciprocal-LUT quality decision:

- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json`
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3.json`

The r3 reciprocal-LUT quality dataset JSON was referenced by review metadata but is not present in
`origin/master`, so the routed estimator command must not depend on that missing path.

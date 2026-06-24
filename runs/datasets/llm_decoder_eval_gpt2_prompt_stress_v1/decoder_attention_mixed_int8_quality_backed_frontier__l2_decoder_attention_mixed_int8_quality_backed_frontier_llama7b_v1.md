# Llama7B Mixed-Int8 Quality-Backed Frontier Audit

- decision: `mixed_int8_quality_backed_frontier_recost_required`
- quality passing candidates: `['qkv8_float_exact']`
- invalidated energy candidates: `1`
- recommended next step: `Recompute the Llama7B energy frontier for q8/k8/v8 projection quantization with high-precision or exact score/softmax PPA; do not rank the old s8/w8 reciprocal-LUT energy row.`

## Quality-Backed Direction

| candidate | status | top1 | top-k | KL | rankable for energy frontier |
|---|---|---:|---:|---:|---|
| qkv8_float_exact | mixed_int8_native_attention_shadow_pass | 1.0 | 1.0 | 0.0012425925766148221 | False |

## Previous Energy Best

| candidate | precision profile | latency us | throughput tok/s | energy mJ | dominant | status |
|---|---|---:|---:|---:|---|---|
| die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024 | q8_k8_v6_a24_s8_w8_recip_lut_q10_int8_compute | 1575.373891 | 634.7699461778119 | 135.75588466251537 | hbm | invalidated for quality-backed ranking |

## Remaining Abstractions

- The quality-passing qkv8_float_exact path has not yet been recosted with matching high-precision/exact score-softmax PPA.
- The previous mixed/int8 energy closure remains useful as a latency/traffic floor only; its s8/w8 reciprocal-LUT score-softmax precision is invalid for quality-backed ranking.
- This audit is an evidence reconciliation step and does not rerun OpenROAD or the native model quality gate.
- HBM/SRAM/NoC abstractions from the source energy closure remain unchanged until the recosted precision path is generated.

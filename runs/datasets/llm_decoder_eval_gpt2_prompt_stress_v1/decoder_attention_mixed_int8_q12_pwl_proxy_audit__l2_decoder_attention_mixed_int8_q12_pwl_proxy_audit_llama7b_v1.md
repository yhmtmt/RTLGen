# llm_decoder_attention_mixed_int8_q12_pwl_proxy_audit_llama7b_v1

- status: `q12_pwl_proxy_quality_rejected`
- recommended_next_step: `Do not use q12/PWL composed proxy as quality-backed for frontier decisions; improve the qkv8_q12_pwl_recip_q12_bucket8 quality gate and top-1/top-k equality before re-running this audit.`

## Quality Candidate

| metric | value |
|---|---|
| candidate_id | qkv8_q12_pwl_recip_q12_bucket8 |
| decision_status | mixed_int8_native_attention_shadow_hold |
| top1_match_rate | 0.96875 |
| topk_contains_rate | 1.0 |
| mean_probability_kl | 0.014237412876954065 |
| quality_pass_for_proxy | False |
| qkv8_float_exact_is_quality_backed_source | True |

## PPA Proxy

| scope | candidate_design | critical_path_ns | die_area | instance_area | total_power_mw |
|---|---|---:|---:|---:|---:|
| composed_q12_pwl | attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12 | 30.8676 | 6250000.0 | 486298.0 | 23.7 |
| full_value_v8 (separate) | attention_kv_full_value_hd64_kv8_v8_tl16_b128_p8_ppc2_w24_a40_wrapper | 0.8825 | 130100.883025 | 0.0 | 0.0339 |

## Remaining Abstractions
- This audit is a measured datapath proxy check, not a full, fully recosted quality-backed frontier decision.
- The composed q12/PWL path is treated as a proxy if not quality-backed by direct qkv8_float_exact service-space evidence.
- Full Llama7B latency/energy/cost ranking remains unchanged until v8 full-value composed PPA replaces this proxy.
- No additional model-level perplexity check is performed in this script.

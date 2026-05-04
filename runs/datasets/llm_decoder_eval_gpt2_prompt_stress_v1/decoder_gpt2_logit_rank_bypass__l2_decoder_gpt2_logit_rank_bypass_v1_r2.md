# Decoder Logit-Rank Bypass

- source_sweep: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_quality_sweep__l2_decoder_gpt2_logit_rank_bypass_v1_r2.json`
- decision: `logit_rank_bypass_exact_safe`
- selected_candidate: `candidate_onnx_logit_rank_bypass`
- reason: Raw-logit ranking matches the reference next-token and top-k gate, so greedy/top-k generation does not need softmax, reciprocal normalization, or probability quantization on this workload.

## Quality

| candidate | next-token | top-k | exact-safe | misses |
|---|---:|---:|---|---|
| `exact_softmax` | 96/96 | 96/96 | `True` | none |
| `logit_rank_bypass` | 96/96 | 96/96 | `True` | none |

## Bypass Scope

- valid_for: `greedy_next_token`, `topk_ranking`, `beam_candidate_ranking`
- not_valid_for: `temperature_sampling`, `top_p_sampling`, `probability_reporting`
- removed: `softmax_exp_or_pwl`, `softmax_sum_normalization`, `reciprocal_normalization`, `probability_quantization`

## Rank Datapath PPA

- status: `measured_logit_rank_datapath`
- source: `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json`
- selected_critical_path_ns: `3.1833`
- selected_die_area: `3738.711025`
- selected_total_power_mw: `0.00348`
- argmax_k1_critical_path_ns: `3.1833`
- argmax_k1_die_area: `3738.711025`
- argmax_k1_total_power_mw: `0.00348`
- topk_k4_critical_path_ns: `3.6015`
- topk_k4_die_area: `8605.345225`
- topk_k4_total_power_mw: `0.0164`
- note: A merged logit-only datapath artifact is used when available. For greedy decoding, the argmax k=1 row is the closest physical proxy; for top-k/beam ranking, the k=4 row is the current measured proxy. Older score/tie-rank artifacts remain accepted only as conservative fallback evidence.

## Next Step

- Use logit-rank bypass as the greedy/top-k architecture path if the evaluator result stays exact-safe.
- Use the measured logit-only argmax/top-k rows in decoder ranking instead of the older score/tie-rank proxy.
- Keep approximate softmax work for sampling modes where calibrated probabilities are required.

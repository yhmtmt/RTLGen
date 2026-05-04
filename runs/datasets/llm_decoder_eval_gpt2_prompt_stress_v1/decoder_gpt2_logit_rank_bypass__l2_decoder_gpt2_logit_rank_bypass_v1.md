# Decoder Logit-Rank Bypass

- source_sweep: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_quality_sweep__l2_decoder_gpt2_logit_rank_bypass_v1.json`
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

## Rank Datapath Proxy

- status: `upper_bound_from_score_tie_rank`
- source: `control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_pwl_tie_rank_datapath_v1_r2.json`
- critical_path_ns: `3.2925`
- die_area: `6786.4644`
- total_power_mw: `0.00526`
- note: The existing score/logit tie-rank block is a conservative rank-like upper bound because raw-logit ranking needs only one comparison key. A dedicated logit-only top-k block should be measured before final array-level PPA claims.

## Next Step

- Use logit-rank bypass as the greedy/top-k architecture path if the evaluator result stays exact-safe.
- Open a dedicated Layer 1 logit-only top-k/argmax datapath measurement before full array-level PPA comparison.
- Keep approximate softmax work for sampling modes where calibrated probabilities are required.

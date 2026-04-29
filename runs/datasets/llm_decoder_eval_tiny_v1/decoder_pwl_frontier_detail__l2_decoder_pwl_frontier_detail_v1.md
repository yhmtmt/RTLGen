# Decoder PWL Frontier Detail

- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json`
- source_cost_proxy: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_survivor_cost_proxy__l2_decoder_survivor_cost_proxy_v1.json`
- decision: `deepen_primary_keep_alternate`
- primary_candidate: `grid_approx_pwl_bf16_path`
- alternate_candidate: `grid_approx_pwl_in_q8_w_q8_norm_exact`

## Frontier Breakdown

| candidate | role | quality | table bits | multiplier out | accumulator | normalization | detail score | previous cost | risk |
|---|---|---|---:|---:|---:|---|---:|---:|---|
| `grid_approx_pwl_bf16_path` | `primary_candidate` | 24/24, 24/24 | 512 | 32 | 22 | `bf16_reciprocal_multiply` | 67.500 | 52.0 | `medium` |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `alternate_frontier` | 24/24, 24/24 | 256 | 16 | 14 | `sum_plus_exact_divide` | 76.500 | 58.0 | `high` |

## Decision

The q8 PWL row has the smaller table and interpolation datapath, but its exact normalization path is the dominant open implementation cost. The bf16 PWL row remains the primary immediate anchor because the prior survivor cost proxy ranked it first and this detailed model isolates normalization as the main reason to keep q8 as a close alternate rather than discard it.

## Next Experiment

- Prototype cost estimates for a bf16 reciprocal PWL decoder softmax block and a q8 PWL exact-normalization block with the same row/token contract.
- Add a q8 PWL reciprocal or bounded-normalization variant only if the quality sweep can keep 24/24 next-token and top-k on the prompt-stress set.
- Escalate the primary candidate to RTL/OpenROAD only after the normalization path is represented explicitly rather than folded into a scalar proxy.

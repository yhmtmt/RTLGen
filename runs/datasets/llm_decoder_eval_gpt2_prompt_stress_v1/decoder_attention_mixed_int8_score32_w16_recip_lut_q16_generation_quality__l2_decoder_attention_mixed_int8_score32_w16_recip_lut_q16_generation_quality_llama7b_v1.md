# Native-Checkpoint Mixed/Int8 Score32 Generation Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_generation_quality_hold`
- next_step: Hold this score32 mixed/int8 generation candidate until a narrower score-precision boundary demonstrates better free-running agreement.

## Candidate Summaries

| candidate_id | status | teacher_forced_nll_delta_mean | cand_ref_prob | free_run_match | first_div_step_mean |
|---|---|---:|---:|---:|---:|
| score32_w16_rtl_recip_q16 | mixed_int8_generation_quality_hold | 1.533711 | 0.251913 | 0.078125 | 0.500000 |

## Prompt Divergence

| candidate_id | prompt_index | first_divergence_step | match_count | steps |
|---|---:|---:|---:|---:|
| score32_w16_rtl_recip_q16 | 0 | 0 | 0 | 8 |
| score32_w16_rtl_recip_q16 | 1 | 0 | 0 | 8 |
| score32_w16_rtl_recip_q16 | 2 | 1 | 1 | 8 |
| score32_w16_rtl_recip_q16 | 3 | 0 | 0 | 8 |
| score32_w16_rtl_recip_q16 | 4 | 1 | 1 | 8 |
| score32_w16_rtl_recip_q16 | 5 | 1 | 2 | 8 |
| score32_w16_rtl_recip_q16 | 6 | 0 | 0 | 8 |
| score32_w16_rtl_recip_q16 | 7 | 1 | 1 | 8 |

## Assumptions

- Teacher-forced rows compare against a non-quantized reference model.
- Candidate applies LLaMA-style q/k/v projection quantization plus softmax approximation.
- Decision thresholds are conservative for score32-vs-reference drift in a bounded prompt sample.

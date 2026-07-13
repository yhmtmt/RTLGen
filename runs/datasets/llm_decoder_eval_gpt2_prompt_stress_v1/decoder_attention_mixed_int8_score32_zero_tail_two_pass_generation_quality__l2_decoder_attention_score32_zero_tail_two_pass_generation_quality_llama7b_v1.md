# Native-Checkpoint Mixed/Int8 Score32 Zero Tail Two Pass Generation Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_generation_quality_pass`
- next_step: Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Candidate Summaries

| candidate_id | status | teacher_forced_nll_delta_mean | cand_ref_prob | free_run_match | first_div_step_mean |
|---|---|---:|---:|---:|---:|
| score32_zero_tail_two_pass | mixed_int8_generation_quality_pass | 0.002160 | 0.447947 | 0.890625 | 7.000000 |

## Prompt Divergence

| candidate_id | prompt_index | first_divergence_step | match_count | steps |
|---|---:|---:|---:|---:|
| score32_zero_tail_two_pass | 0 | 8 | 8 | 8 |
| score32_zero_tail_two_pass | 1 | 8 | 8 | 8 |
| score32_zero_tail_two_pass | 2 | 8 | 8 | 8 |
| score32_zero_tail_two_pass | 3 | 0 | 1 | 8 |
| score32_zero_tail_two_pass | 4 | 8 | 8 | 8 |
| score32_zero_tail_two_pass | 5 | 8 | 8 | 8 |
| score32_zero_tail_two_pass | 6 | 8 | 8 | 8 |
| score32_zero_tail_two_pass | 7 | 8 | 8 | 8 |

## Assumptions

- Teacher-forced rows compare against a non-quantized reference model.
- Candidate applies LLaMA-style q/k/v projection quantization plus softmax approximation.
- Decision thresholds are conservative for Score32 Zero Tail Two Pass-vs-reference drift in a bounded prompt sample.

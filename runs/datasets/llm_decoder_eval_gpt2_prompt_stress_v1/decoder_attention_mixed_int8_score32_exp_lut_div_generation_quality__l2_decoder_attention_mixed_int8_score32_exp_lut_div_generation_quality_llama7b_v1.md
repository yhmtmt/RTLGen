# Native-Checkpoint Mixed/Int8 Score32 Exp LUT Div Generation Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `mixed_int8_generation_quality_pass`
- next_step: Candidate passed the bounded generation-quality gate; route this score configuration into the native-checkpoint quality evidence stream.

## Candidate Summaries

| candidate_id | status | teacher_forced_nll_delta_mean | cand_ref_prob | free_run_match | first_div_step_mean |
|---|---|---:|---:|---:|---:|
| score32_exp_lut_div | mixed_int8_generation_quality_pass | 0.000895 | 0.448890 | 0.890625 | 7.000000 |

## Prompt Divergence

| candidate_id | prompt_index | first_divergence_step | match_count | steps |
|---|---:|---:|---:|---:|
| score32_exp_lut_div | 0 | 8 | 8 | 8 |
| score32_exp_lut_div | 1 | 8 | 8 | 8 |
| score32_exp_lut_div | 2 | 8 | 8 | 8 |
| score32_exp_lut_div | 3 | 0 | 1 | 8 |
| score32_exp_lut_div | 4 | 8 | 8 | 8 |
| score32_exp_lut_div | 5 | 8 | 8 | 8 |
| score32_exp_lut_div | 6 | 8 | 8 | 8 |
| score32_exp_lut_div | 7 | 8 | 8 | 8 |

## Assumptions

- Teacher-forced rows compare against a non-quantized reference model.
- Candidate applies LLaMA-style q/k/v projection quantization plus softmax approximation.
- Decision thresholds are conservative for Score32 Exp LUT Div-vs-reference drift in a bounded prompt sample.

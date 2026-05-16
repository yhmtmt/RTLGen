# Decoder Attention/KV Quality Gate

- model: `llm_decoder_attention_kv_quality_gate_v1`
- candidate_row_count: `36`
- primary_hardware_candidate: `gqa8_kv8`
- primary_quality_experiment: `gqa8_kv4`
- bound_only_candidate: `mqa_kv4`

## Recommendation

MQA/KV4 is the strongest hardware lower bound, but both dimensions carry high quality risk. GQA8/KV8 is the conservative structural candidate; GQA8/KV4 is the useful quality experiment for testing whether low-bit KV can recover enough of the HBM benefit without changing to MQA.

## Practical Candidates

| seq | die | kv | bits | latency_us | speedup | hbm_share | risk | class |
|---:|---:|---|---:|---:|---:|---:|---|---|
| 131072 | 400.0 | gqa8 | 8 | 119.84 | 16.801602 | 0.816646 | medium | deployable_if_model_supports_structure |
| 131072 | 200.0 | gqa8 | 8 | 131.488 | 15.401801 | 0.908323 | medium | deployable_if_model_supports_structure |
| 131072 | 100.0 | gqa8 | 8 | 137.696 | 14.752498 | 0.954161 | medium | deployable_if_model_supports_structure |
| 131072 | 400.0 | gqa4 | 8 | 246.304 | 8.174873 | 0.908323 | medium | deployable_if_model_supports_structure |
| 131072 | 400.0 | gqa8 | 16 | 246.304 | 8.174873 | 0.908323 | medium | deployable_if_model_supports_structure |
| 131072 | 200.0 | gqa4 | 8 | 257.952 | 7.850887 | 0.954161 | medium | deployable_if_model_supports_structure |
| 131072 | 200.0 | gqa8 | 16 | 257.952 | 7.850887 | 0.954161 | medium | deployable_if_model_supports_structure |
| 131072 | 100.0 | gqa4 | 8 | 264.16 | 7.689885 | 0.977081 | medium | deployable_if_model_supports_structure |
| 131072 | 100.0 | gqa8 | 16 | 264.16 | 7.689885 | 0.977081 | medium | deployable_if_model_supports_structure |
| 131072 | 400.0 | gqa4 | 16 | 498.784 | 4.036826 | 0.954161 | medium | deployable_if_model_supports_structure |

## Quality Experiments

| seq | die | kv | bits | latency_us | speedup | hbm_share | risk |
|---:|---:|---|---:|---:|---:|---:|---|
| 131072 | 400.0 | gqa8 | 4 | 79.648 | 25.280032 | 0.633292 | high |
| 131072 | 200.0 | gqa8 | 4 | 79.84 | 25.36513 | 0.816646 | high |
| 131072 | 100.0 | gqa8 | 4 | 80.064 | 25.371703 | 0.908323 | high |
| 131072 | 400.0 | gqa4 | 4 | 119.84 | 16.801602 | 0.816646 | high |
| 131072 | 200.0 | gqa4 | 4 | 131.488 | 15.401801 | 0.908323 | high |
| 131072 | 100.0 | gqa4 | 4 | 137.696 | 14.752498 | 0.954161 | high |
| 131072 | 400.0 | mha | 4 | 498.784 | 4.036826 | 0.954161 | high |
| 131072 | 200.0 | mha | 4 | 510.432 | 3.967526 | 0.977081 | high |
| 131072 | 100.0 | mha | 4 | 515.872 | 3.937721 | 0.98854 | high |

## Bound Only

| seq | die | kv | bits | latency_us | speedup | hbm_share | reason |
|---:|---:|---|---:|---:|---:|---:|---|
| 131072 | 100.0 | mqa | 4 | 79.136 | 25.669228 | 0.633292 | collapses all K/V heads and should be treated as retraining-required; low-bit KV cache can perturb attention scores and retrieval behavior |
| 131072 | 100.0 | mqa | 8 | 79.136 | 25.669228 | 0.816646 | collapses all K/V heads and should be treated as retraining-required; plausible cache quantization, but must be checked on long-context prompts |
| 131072 | 200.0 | mqa | 4 | 79.232 | 25.559774 | 0.266583 | collapses all K/V heads and should be treated as retraining-required; low-bit KV cache can perturb attention scores and retrieval behavior |
| 131072 | 200.0 | mqa | 8 | 79.232 | 25.559774 | 0.633292 | collapses all K/V heads and should be treated as retraining-required; plausible cache quantization, but must be checked on long-context prompts |
| 131072 | 400.0 | mqa | 4 | 79.328 | 25.382009 | 0.0 | collapses all K/V heads and should be treated as retraining-required; low-bit KV cache can perturb attention scores and retrieval behavior |
| 131072 | 400.0 | mqa | 8 | 79.456 | 25.34112 | 0.266583 | collapses all K/V heads and should be treated as retraining-required; plausible cache quantization, but must be checked on long-context prompts |
| 131072 | 400.0 | mqa | 16 | 79.456 | 25.34112 | 0.633292 | collapses all K/V heads and should be treated as retraining-required; keeps baseline KV precision |
| 131072 | 200.0 | mqa | 16 | 79.84 | 25.36513 | 0.816646 | collapses all K/V heads and should be treated as retraining-required; keeps baseline KV precision |
| 131072 | 100.0 | mqa | 16 | 80.064 | 25.371703 | 0.908323 | collapses all K/V heads and should be treated as retraining-required; keeps baseline KV precision |

## Assumptions

- This gate does not claim measured LLaMA quality; it prevents hardware-only winners from being treated as deployable.
- GQA candidates require a model trained or adapted for grouped-query attention before deployment.
- MQA candidates are classified as bound-only unless a retrained/adapted model is supplied.
- KV4 candidates require long-context quality and retrieval-stability experiments before they can be promoted.
- The hardware benefit values come from the merged physical-HBM frontier artifact.

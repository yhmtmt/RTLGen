# Native GQA KV Quantization Quality

- model_id: `mistralai/Mistral-7B-v0.1`
- decision: `native_checkpoint_kv4_promising`
- next_step: Use this checkpoint evidence with the PPA model, then schedule a larger 7B-class or QAT confirmation.

## Model

- attention_heads: `32`
- kv_heads: `8`
- gqa_group_size: `4.0`

## Candidates

| kv_bits | granularity | comparisons | top1 | topk | cosine | kl | min_margin | max_delta |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | tensor | 8 | 1.000000 | 1.000000 | 0.999954 | 0.000480 | 0.000000 | 0.437500 |
| 4 | tensor | 8 | 1.000000 | 1.000000 | 0.997820 | 0.016785 | 0.000000 | 2.312500 |

## Cautions

- Best KV4 ranking mostly holds, but logit cosine is below the promotion caution line

## Assumptions

- This is post-training native-checkpoint KV cache quantization, not QAT.
- Teacher-forced reference tokens isolate KV-cache perturbation from divergent generated text.
- The evaluator must have Hugging Face model access; generated model weights are not committed.

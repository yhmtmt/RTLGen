# Native GQA KV Quantization Quality

- model_id: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- decision: `hold_for_qat_or_safer_kv_format`
- next_step: Run QAT/fine-tuning recovery or move the frontier back to KV8 for the native GQA checkpoint.

## Model

- attention_heads: `32`
- kv_heads: `4`
- gqa_group_size: `8.0`

## Candidates

| kv_bits | comparisons | top1 | topk | cosine | kl | min_margin | max_delta |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 64 | 1.000000 | 1.000000 | 0.999919 | 0.001168 | 0.018651 | 0.522902 |
| 4 | 64 | 0.750000 | 0.937500 | 0.985063 | 0.236089 | 0.018651 | 6.787605 |

## Blockers

- KV4 changed too many native-checkpoint next-token rankings

## Assumptions

- This is post-training native-checkpoint KV cache quantization, not QAT.
- Teacher-forced reference tokens isolate KV-cache perturbation from divergent generated text.
- The evaluator must have Hugging Face model access; generated model weights are not committed.

# Decoder Attention/KV Trace Calibration

- model: `llm_decoder_attention_kv_trace_calibration_v1`
- decision: `advance_model_native_gqa_kv4_quality_run`
- next_step: Schedule a real model-native or QAT GQA8/KV4 quality run; include low-margin and KV-outlier prompt regimes.

## Native Proxy

| candidate | decision | top1 | cosine | rmse |
|---|---|---:|---:|---:|
| gqa8_kv8 | native_proxy_risk | 0.994792 | 0.999987 | 0.001301 |
| gqa8_kv4 | native_lowbit_promising | 0.992188 | 0.995913 | 0.023591 |

## Low-Margin Native Regime

- gqa8_kv4 low-margin top1: `0.976562`
- gqa8_kv4 low-margin cosine: `0.993253`

## Trained-Checkpoint KV4 Trace Controls

| label | samples | next | topk | tensors | mean_delta | max_tensor_mean_delta | p95_scale | max_abs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt2_prompt_stress | 96 | 1.0 | 1.0 | 2304 | 0.003173901 | 0.024132296 | 2.285823822 | 21.790367126 |
| distilgpt2_prompt_stress | 96 | 1.0 | 1.0 | 1152 | 0.002614696 | 0.016192868 | 1.643620627 | 16.020776749 |

## Cautions

- native low-margin synthetic regime remains sensitive and must be included in the next real-model dataset

## Assumptions

- The trained-checkpoint trace inputs are GPT-2-family MHA controls, not native GQA model quality.
- The trace calibration checks whether existing real-checkpoint KV4 tensor quantization error is in-family with the synthetic native GQA/KV4 proxy.
- A pass only schedules a model-native or QAT GQA8/KV4 quality run; it does not promote GQA8/KV4 as deployable.

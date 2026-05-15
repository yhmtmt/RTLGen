# Decoder Stage Breakdown

- model: `llm_decoder_stage_breakdown_v1`

## Focus Summary

| shape | seq | weight model | total_us | dominant | share | attention | mlp | output_projection | ranker |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|
| gpt2_medium_proxy | 128 | resident_weights | 360.995 | ranker | 0.836089 | 0.140412 | 0.01702 | 0.004352 | 0.836089 |
| gpt2_medium_proxy | 128 | streaming_weights | 3116.761 | mlp | 0.505201 | 0.268587 | 0.505201 | 0.129127 | 0.096839 |
| gpt2_medium_proxy | 512 | resident_weights | 508.451 | ranker | 0.593615 | 0.389701 | 0.012084 | 0.00309 | 0.593615 |
| gpt2_medium_proxy | 512 | streaming_weights | 3264.217 | mlp | 0.48238 | 0.301627 | 0.48238 | 0.123294 | 0.092464 |
| gpt2_medium_proxy | 2048 | resident_weights | 1098.275 | attention | 0.71746 | 0.71746 | 0.005594 | 0.00143 | 0.274816 |
| gpt2_medium_proxy | 2048 | streaming_weights | 3854.041 | mlp | 0.408556 | 0.408506 | 0.408556 | 0.104425 | 0.078314 |
| gpt2_medium_proxy | 8192 | resident_weights | 3457.571 | attention | 0.910253 | 0.910253 | 0.001777 | 0.000454 | 0.087294 |
| gpt2_medium_proxy | 8192 | streaming_weights | 6213.337 | attention | 0.633105 | 0.633105 | 0.253421 | 0.064773 | 0.048577 |
| gpt2_small | 128 | resident_weights | 324.026 | ranker | 0.931481 | 0.058662 | 0.005333 | 0.003636 | 0.931481 |
| gpt2_small | 128 | streaming_weights | 1287.261 | mlp | 0.344154 | 0.186592 | 0.344154 | 0.234561 | 0.23447 |
| gpt2_small | 512 | resident_weights | 379.322 | ranker | 0.795693 | 0.195886 | 0.004555 | 0.003106 | 0.795693 |
| gpt2_small | 512 | streaming_weights | 1342.557 | mlp | 0.329979 | 0.220093 | 0.329979 | 0.2249 | 0.224813 |
| gpt2_small | 2048 | resident_weights | 600.506 | ranker | 0.502616 | 0.492065 | 0.002878 | 0.001962 | 0.502616 |
| gpt2_small | 2048 | streaming_weights | 1563.741 | attention | 0.330408 | 0.330408 | 0.283305 | 0.193089 | 0.193014 |
| gpt2_small | 8192 | resident_weights | 1485.242 | attention | 0.794634 | 0.794634 | 0.001163 | 0.000793 | 0.203215 |
| gpt2_small | 8192 | streaming_weights | 2448.477 | attention | 0.572359 | 0.572359 | 0.180935 | 0.123318 | 0.12327 |
| large_vocab_proxy | 128 | resident_weights | 776.426 | ranker | 0.773019 | 0.17409 | 0.042204 | 0.00805 | 0.773019 |
| large_vocab_proxy | 128 | streaming_weights | 14925.726 | mlp | 0.562332 | 0.290068 | 0.562332 | 0.107251 | 0.040212 |
| large_vocab_proxy | 512 | resident_weights | 1169.642 | ranker | 0.513142 | 0.451748 | 0.028015 | 0.005344 | 0.513142 |
| large_vocab_proxy | 512 | streaming_weights | 15318.942 | mlp | 0.547898 | 0.308291 | 0.547898 | 0.104498 | 0.03918 |
| large_vocab_proxy | 2048 | resident_weights | 2742.506 | attention | 0.766178 | 0.766178 | 0.011948 | 0.002279 | 0.218848 |
| large_vocab_proxy | 2048 | streaming_weights | 16891.806 | mlp | 0.496881 | 0.372699 | 0.496881 | 0.094768 | 0.035532 |
| large_vocab_proxy | 8192 | resident_weights | 9033.962 | attention | 0.929017 | 0.929017 | 0.003627 | 0.000692 | 0.066437 |
| large_vocab_proxy | 8192 | streaming_weights | 23183.262 | attention | 0.542935 | 0.542935 | 0.362038 | 0.06905 | 0.025889 |
| long_context_proxy | 128 | resident_weights | 1630.504 | ranker | 0.735969 | 0.165799 | 0.080387 | 0.015333 | 0.735969 |
| long_context_proxy | 128 | streaming_weights | 58216.891 | mlp | 0.576528 | 0.292828 | 0.576528 | 0.109961 | 0.020613 |
| long_context_proxy | 512 | resident_weights | 2416.936 | ranker | 0.496496 | 0.437235 | 0.054231 | 0.010344 | 0.496496 |
| long_context_proxy | 512 | streaming_weights | 59003.323 | mlp | 0.568843 | 0.302254 | 0.568843 | 0.108495 | 0.020338 |
| long_context_proxy | 2048 | resident_weights | 5562.664 | attention | 0.755483 | 0.755483 | 0.023563 | 0.004494 | 0.215724 |
| long_context_proxy | 2048 | streaming_weights | 62149.051 | mlp | 0.540051 | 0.337571 | 0.540051 | 0.103004 | 0.019308 |
| long_context_proxy | 8192 | resident_weights | 18145.576 | attention | 0.925041 | 0.925041 | 0.007223 | 0.001378 | 0.066132 |
| long_context_proxy | 8192 | streaming_weights | 74731.963 | mlp | 0.44912 | 0.449107 | 0.44912 | 0.085661 | 0.016057 |

## Assumptions

- This is a rough stage-serialized single-token decode model, not measured RTL.
- Attention includes QKV projection, QK score, value mix, and output projection.
- MLP uses a two-projection feed-forward block with ffn_multiplier expansion.
- streaming_weights charges decoder and output-projection weights each token.
- resident_weights removes weight traffic to expose compute and KV-cache sensitivity.
- Ranker is a rough standalone streaming bound; producer-integrated RTL/PPA remains authoritative.

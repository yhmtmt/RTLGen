# Decoder Stage Breakdown

- model: `llm_decoder_stage_breakdown_v1`

## Focus Summary

| shape | seq | weight model | total_us | dominant | share | attention | mlp | output_projection | ranker |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|
| gpt2_medium_proxy | 2048 | resident_weights | 499.541 | ranker | 0.604203 | 0.394346 | 0.000865 | 0.000202 | 0.604203 |
| gpt2_medium_proxy | 2048 | streaming_weights | 1189.879 | mlp | 0.33083 | 0.33079 | 0.33083 | 0.084559 | 0.253659 |
| gpt2_medium_proxy | 8192 | resident_weights | 1089.365 | attention | 0.72227 | 0.72227 | 0.000397 | 9.3e-05 | 0.277064 |
| gpt2_medium_proxy | 8192 | streaming_weights | 1779.703 | attention | 0.552578 | 0.552578 | 0.221187 | 0.056535 | 0.169592 |
| gpt2_medium_proxy | 32768 | resident_weights | 3448.661 | attention | 0.912271 | 0.912271 | 0.000125 | 2.9e-05 | 0.087519 |
| gpt2_medium_proxy | 32768 | streaming_weights | 4138.999 | attention | 0.807616 | 0.807616 | 0.095107 | 0.024309 | 0.072922 |
| gpt2_medium_proxy | 131072 | resident_weights | 12885.845 | attention | 0.976521 | 0.976521 | 3.4e-05 | 8e-06 | 0.023423 |
| gpt2_medium_proxy | 131072 | streaming_weights | 13576.183 | attention | 0.941347 | 0.941347 | 0.028995 | 0.007411 | 0.022232 |
| gpt2_small | 2048 | resident_weights | 376.03 | ranker | 0.802659 | 0.196452 | 0.000431 | 0.000266 | 0.802659 |
| gpt2_small | 2048 | streaming_weights | 617.304 | ranker | 0.488939 | 0.209245 | 0.179416 | 0.122283 | 0.488939 |
| gpt2_small | 8192 | resident_weights | 597.214 | ranker | 0.505387 | 0.494054 | 0.000271 | 0.000167 | 0.505387 |
| gpt2_small | 8192 | streaming_weights | 838.488 | attention | 0.417838 | 0.417838 | 0.132088 | 0.090026 | 0.359962 |
| gpt2_small | 32768 | resident_weights | 1481.95 | attention | 0.796108 | 0.796108 | 0.000109 | 6.7e-05 | 0.203667 |
| gpt2_small | 32768 | streaming_weights | 1723.224 | attention | 0.716731 | 0.716731 | 0.064271 | 0.043805 | 0.175151 |
| gpt2_small | 131072 | resident_weights | 5020.894 | attention | 0.93982 | 0.93982 | 3.2e-05 | 2e-05 | 0.060114 |
| gpt2_small | 131072 | streaming_weights | 5262.168 | attention | 0.907237 | 0.907237 | 0.021047 | 0.014345 | 0.057357 |
| large_vocab_proxy | 2048 | resident_weights | 1128.455 | ranker | 0.531871 | 0.465514 | 0.001815 | 0.000346 | 0.531871 |
| large_vocab_proxy | 2048 | streaming_weights | 4673.096 | mlp | 0.449018 | 0.336798 | 0.449018 | 0.085639 | 0.128436 |
| large_vocab_proxy | 8192 | resident_weights | 2701.319 | attention | 0.776723 | 0.776723 | 0.000758 | 0.000145 | 0.222185 |
| large_vocab_proxy | 8192 | streaming_weights | 6245.96 | attention | 0.503806 | 0.503806 | 0.335946 | 0.064073 | 0.096093 |
| large_vocab_proxy | 32768 | resident_weights | 8992.775 | attention | 0.93293 | 0.93293 | 0.000228 | 4.3e-05 | 0.066742 |
| large_vocab_proxy | 32768 | streaming_weights | 12537.416 | attention | 0.752803 | 0.752803 | 0.167363 | 0.03192 | 0.047872 |
| large_vocab_proxy | 131072 | resident_weights | 34158.599 | attention | 0.982343 | 0.982343 | 6e-05 | 1.1e-05 | 0.017571 |
| large_vocab_proxy | 131072 | streaming_weights | 37703.24 | attention | 0.9178 | 0.9178 | 0.055653 | 0.010614 | 0.015919 |
| long_context_proxy | 2048 | resident_weights | 2261.403 | ranker | 0.530644 | 0.464589 | 0.003623 | 0.000691 | 0.530644 |
| long_context_proxy | 2048 | streaming_weights | 16437.263 | mlp | 0.510481 | 0.319088 | 0.510481 | 0.097364 | 0.073005 |
| long_context_proxy | 8192 | resident_weights | 5407.131 | attention | 0.776077 | 0.776077 | 0.001515 | 0.000289 | 0.221929 |
| long_context_proxy | 8192 | streaming_weights | 19582.991 | mlp | 0.42848 | 0.428467 | 0.42848 | 0.081724 | 0.061278 |
| long_context_proxy | 32768 | resident_weights | 17990.043 | attention | 0.932697 | 0.932697 | 0.000455 | 8.7e-05 | 0.066704 |
| long_context_proxy | 32768 | streaming_weights | 32165.903 | attention | 0.652044 | 0.652044 | 0.260864 | 0.049755 | 0.037307 |
| long_context_proxy | 131072 | resident_weights | 68321.691 | attention | 0.982278 | 0.982278 | 0.00012 | 2.3e-05 | 0.017564 |
| long_context_proxy | 131072 | streaming_weights | 82497.551 | attention | 0.864331 | 0.864331 | 0.101711 | 0.019399 | 0.014546 |

## Assumptions

- This is a rough stage-serialized single-token decode model, not measured RTL.
- Attention includes QKV projection, QK score, value mix, and output projection.
- MLP uses a two-projection feed-forward block with ffn_multiplier expansion.
- streaming_weights charges decoder and output-projection weights each token.
- resident_weights removes weight traffic to expose compute and KV-cache sensitivity.
- Ranker is a rough standalone streaming bound; producer-integrated RTL/PPA remains authoritative.

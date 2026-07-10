# Separated Attention Perf/RTL Equivalence

- decision: `attention_separated_cluster_equivalence_pass`
- equivalence pass: `True`
- semantic profile: `q8_k8_v8_a32_s32_w16_exp_lut_div_b20`

| ratio | scenario | pass | completed | final cycle |
|---|---|---:|---:|---:|
| 1:1 | always_ready | True | 8 | 16 |
| 1:1 | intermittent_consumer_stall | True | 8 | 17 |
| 1:1 | all_consumers_blocked_temporarily | True | 8 | 19 |
| 1:1 | result_backpressure | True | 8 | 21 |
| 2:1 | always_ready | True | 8 | 16 |
| 2:1 | intermittent_consumer_stall | True | 8 | 17 |
| 2:1 | all_consumers_blocked_temporarily | True | 8 | 19 |
| 2:1 | result_backpressure | True | 8 | 21 |
| 4:1 | always_ready | True | 8 | 16 |
| 4:1 | intermittent_consumer_stall | True | 8 | 17 |
| 4:1 | all_consumers_blocked_temporarily | True | 8 | 19 |
| 4:1 | result_backpressure | True | 8 | 21 |
| 8:1 | always_ready | True | 8 | 16 |
| 8:1 | intermittent_consumer_stall | True | 8 | 17 |
| 8:1 | all_consumers_blocked_temporarily | True | 8 | 19 |
| 8:1 | result_backpressure | True | 8 | 21 |
| 4:2 | always_ready | True | 8 | 9 |
| 4:2 | intermittent_consumer_stall | True | 8 | 9 |
| 4:2 | all_consumers_blocked_temporarily | True | 8 | 13 |
| 4:2 | result_backpressure | True | 8 | 14 |
| 8:2 | always_ready | True | 8 | 9 |
| 8:2 | intermittent_consumer_stall | True | 8 | 9 |
| 8:2 | all_consumers_blocked_temporarily | True | 8 | 13 |
| 8:2 | result_backpressure | True | 8 | 14 |

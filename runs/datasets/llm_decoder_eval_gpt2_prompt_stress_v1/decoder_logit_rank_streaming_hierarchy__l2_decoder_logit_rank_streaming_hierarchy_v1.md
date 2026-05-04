# Decoder Logit-Rank Streaming Hierarchy

- model: `decoder_logit_rank_streaming_hierarchy_v1`
- rank_ppa_paths: `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json, control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json`
- recommendation: `flat_measured_ranker_scan`
- merge_variant: ``
- latency_us_per_token: `20.010224`
- tokens_per_s: `49974.454`
- fifo_capacity_ok: `True`
- reason: Lowest modelled latency per token among FIFO-valid measured flat scans and hierarchical streaming alternatives.

## Inputs

| input | value |
|---|---:|
| `rank_ppa_path` | `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json` |
| `scale_ppa_path` | `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json` |
| `prompt_stress_path` | `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_gpt2_prompt_stress__l2_decoder_gpt2_prompt_stress_v1.json` |
| `logit_rank_bypass_path` | `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_gpt2_logit_rank_bypass__l2_decoder_gpt2_logit_rank_bypass_v1.json` |
| `vocab_size` | `50257` |
| `producer_lanes` | `8` |
| `top_k` | `4` |
| `producer_latency_cycles` | `1` |
| `producer_ii_cycles` | `1` |
| `local_ranker_latency_cycles` | `4` |
| `local_ranker_ii_cycles` | `1` |
| `global_merge_latency_cycles` | `3` |
| `global_merge_ii_cycles_list` | `[1, 2, 4]` |
| `candidate_fifo_depth_groups` | `16` |
| `fallback_critical_path_ns` | `3.6` |

## Flat Measured Ranker Points

| lanes | top_k | cycles | latency_us | tokens_per_s | critical_path_ns | source |
|---:|---:|---:|---:|---:|---:|---|
| 8 | 1 | 6286 | 20.010224 | 49974.454 | 3.1833 | `runs/designs/activations/logit_rank_r8_l16_k1_wrapper/metrics.csv` |
| 8 | 4 | 6286 | 22.639029 | 44171.506 | 3.6015 | `runs/designs/activations/logit_rank_r8_l16_k4_wrapper/metrics.csv` |
| 16 | 1 | 3145 | 21.836678 | 45794.51 | 6.9433 | `runs/designs/activations/logit_rank_r16_l16_k1_wrapper/metrics.csv` |
| 16 | 4 | 3145 | 24.783544 | 40349.355 | 7.8803 | `runs/designs/activations/logit_rank_r16_l16_k4_wrapper/metrics.csv` |
| 32 | 1 | 1574 | 21.957457 | 45542.614 | 13.9501 | `runs/designs/activations/logit_rank_r32_l16_k1_wrapper/metrics.csv` |
| 32 | 4 | 1574 | 24.342854 | 41079.817 | 15.4656 | `runs/designs/activations/logit_rank_r32_l16_k4_wrapper/metrics.csv` |

## Hierarchical Streaming Alternatives

| variant | W | top_k | cycles | latency_us | tokens_per_s | fifo required/capacity | fifo ok | speedup vs flat |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| `merge_ii_1` | 8 | 4 | 6290 | 22.653435 | 44143.416 | 1/16 | `True` | 0.88332 |
| `merge_ii_2` | 8 | 4 | 12572 | 45.278058 | 22085.753 | 3142/16 | `False` | 0.441941 |
| `merge_ii_4` | 8 | 4 | 25136 | 90.527304 | 11046.391 | 4712/16 | `False` | 0.221041 |

## Assumptions

- Producer emits one W-lane logit tile after producer latency and then every producer II cycles.
- Local ranker accepts one producer tile per local ranker II and emits one candidate group after local ranker latency.
- Candidate FIFO depth is reported in local candidate groups; overflow is reported as capacity evidence, not hidden by backpressure.
- Global merge consumes one local candidate group per merge II and produces the final token rank after the last merge latency.
- Measured row-8 datapath and row-16/row-32 scale critical_path_ns values are used as ranker clock proxies.
- Missing lane points are explicit defaults or log2-lane scaled proxies.

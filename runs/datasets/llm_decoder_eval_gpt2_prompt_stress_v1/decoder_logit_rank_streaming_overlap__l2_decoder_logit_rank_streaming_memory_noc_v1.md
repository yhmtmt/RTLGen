# Decoder Logit-Rank Streaming Hierarchy

- model: `decoder_logit_rank_streaming_hierarchy_v1`
- rank_ppa_paths: `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json, control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json, control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json`
- recommendation: `flat_measured_ranker_scan`
- merge_variant: ``
- latency_us_per_token: `20.010224`
- tokens_per_s: `49974.454`
- fifo_capacity_ok: `True`
- reason: Lowest modelled latency per token among FIFO-valid measured flat scans and hierarchical streaming alternatives.
- overlap_sweep_best: `w8_k1_prodii1_mergeii1_fifo16`
- overlap_recovered_fraction: `0.499682`
- traffic_reduction_vs_materialized: `0.749945`
- memory_traffic_best: `w32_k1_prodii1_mergeii1_fifo16`
- memory_total_bytes: `12572`
- memory_bound_latency_us: `22.013258`

## Inputs

| input | value |
|---|---:|
| `rank_ppa_path` | `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_datapath_v1_r2.json` |
| `scale_ppa_path` | `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json` |
| `candidate_merge_ppa_path` | `control_plane/shadow_exports/l1_promotions/l1_decoder_candidate_stream_merge_fifo_v1.json` |
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
| `producer_lanes_list` | `[8, 16, 32]` |
| `top_k_list` | `[1, 4]` |
| `producer_ii_cycles_list` | `[1, 2, 4]` |
| `candidate_fifo_depth_groups_list` | `[16, 256, 4096]` |
| `token_id_bits` | `16` |
| `fallback_critical_path_ns` | `3.6` |
| `memory_bandwidth_bytes_per_cycle` | `64.0` |
| `sram_read_energy_pj_per_byte` | `0.05` |
| `sram_write_energy_pj_per_byte` | `0.07` |
| `noc_hops` | `2` |
| `noc_energy_pj_per_byte_hop` | `0.02` |

## Flat Measured Ranker Points

| lanes | top_k | cycles | latency_us | memory_bytes | memory_bound_us | tokens_per_s | critical_path_ns | source |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 8 | 1 | 6286 | 20.010224 | 201028 | 20.010224 | 49974.454 | 3.1833 | `runs/designs/activations/logit_rank_r8_l16_k1_wrapper/metrics.csv` |
| 8 | 4 | 6286 | 22.639029 | 201028 | 22.639029 | 44171.506 | 3.6015 | `runs/designs/activations/logit_rank_r8_l16_k4_wrapper/metrics.csv` |
| 16 | 1 | 3145 | 21.836678 | 201028 | 21.836678 | 45794.51 | 6.9433 | `runs/designs/activations/logit_rank_r16_l16_k1_wrapper/metrics.csv` |
| 16 | 4 | 3145 | 24.783544 | 201028 | 24.783544 | 40349.355 | 7.8803 | `runs/designs/activations/logit_rank_r16_l16_k4_wrapper/metrics.csv` |
| 32 | 1 | 1574 | 21.957457 | 201028 | 43.831214 | 45542.614 | 13.9501 | `runs/designs/activations/logit_rank_r32_l16_k1_wrapper/metrics.csv` |
| 32 | 4 | 1574 | 24.342854 | 201028 | 48.592915 | 41079.817 | 15.4656 | `runs/designs/activations/logit_rank_r32_l16_k4_wrapper/metrics.csv` |

## Hierarchical Streaming Alternatives

| variant | W | top_k | cycles | latency_us | memory_bytes | memory_bound_us | tokens_per_s | merge_fifo_cp_ns | est_area | fifo required/capacity | fifo ok | speedup vs flat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| `merge_ii_1` | 8 | 4 | 6290 | 22.653435 | 201072 | 22.653435 | 44143.416 | 3.1012 | 51504.039625 | 1/16 | `True` | 0.88332 |
| `merge_ii_2` | 8 | 4 | 12572 | 45.278058 | 201072 | 45.278058 | 22085.753 | 3.1012 | 51504.039625 | 3142/16 | `False` | 0.441941 |
| `merge_ii_4` | 8 | 4 | 25136 | 90.527304 | 201072 | 90.527304 | 11046.391 | 3.1012 | 51504.039625 | 4712/16 | `False` | 0.221041 |

## Overlap And Traffic Sweep

| key | cycles | latency_us | memory_bytes | memory_energy_nj | fifo required/capacity | overlap recovered | traffic reduction | speedup vs flat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `w8_k1_prodii1_mergeii1_fifo16` | 6290 | 20.022957 | 50268 | 5.02684 | 1/16 | 0.499682 | 0.749945 | 0.999364 |
| `w8_k1_prodii1_mergeii1_fifo256` | 6290 | 20.022957 | 50268 | 5.02684 | 1/256 | 0.499682 | 0.749945 | 0.999364 |
| `w8_k1_prodii1_mergeii1_fifo4096` | 6290 | 20.022957 | 50268 | 5.02684 | 1/4096 | 0.499682 | 0.749945 | 0.999364 |
| `w8_k1_prodii1_mergeii2_fifo16` | 12572 | 40.020448 | 50268 | 5.02684 | 3142/16 | 0.0 | 0.749945 | 0.5 |
| `w8_k1_prodii1_mergeii2_fifo256` | 12572 | 40.020448 | 50268 | 5.02684 | 3142/256 | 0.0 | 0.749945 | 0.5 |
| `w8_k1_prodii1_mergeii2_fifo4096` | 12572 | 40.020448 | 50268 | 5.02684 | 3142/4096 | 0.0 | 0.749945 | 0.5 |
| `w8_k1_prodii1_mergeii4_fifo16` | 25136 | 80.015429 | 50268 | 5.02684 | 4712/16 | 0.0 | 0.749945 | 0.25008 |
| `w8_k1_prodii1_mergeii4_fifo256` | 25136 | 80.015429 | 50268 | 5.02684 | 4712/256 | 0.0 | 0.749945 | 0.25008 |
| `w8_k1_prodii1_mergeii4_fifo4096` | 25136 | 80.015429 | 50268 | 5.02684 | 4712/4096 | 0.0 | 0.749945 | 0.25008 |
| `w8_k1_prodii2_mergeii1_fifo16` | 12572 | 40.020448 | 50268 | 5.02684 | 1/16 | 0.333192 | 0.749945 | 0.5 |
| `w8_k1_prodii2_mergeii1_fifo256` | 12572 | 40.020448 | 50268 | 5.02684 | 1/256 | 0.333192 | 0.749945 | 0.5 |
| `w8_k1_prodii2_mergeii1_fifo4096` | 12572 | 40.020448 | 50268 | 5.02684 | 1/4096 | 0.333192 | 0.749945 | 0.5 |
| `w8_k1_prodii2_mergeii2_fifo16` | 12572 | 40.020448 | 50268 | 5.02684 | 1/16 | 0.333192 | 0.749945 | 0.5 |
| `w8_k1_prodii2_mergeii2_fifo256` | 12572 | 40.020448 | 50268 | 5.02684 | 1/256 | 0.333192 | 0.749945 | 0.5 |
| `w8_k1_prodii2_mergeii2_fifo4096` | 12572 | 40.020448 | 50268 | 5.02684 | 1/4096 | 0.333192 | 0.749945 | 0.5 |
| `w8_k1_prodii2_mergeii4_fifo16` | 25136 | 80.015429 | 50268 | 5.02684 | 3142/16 | 0.0 | 0.749945 | 0.25008 |
| `w8_k1_prodii2_mergeii4_fifo256` | 25136 | 80.015429 | 50268 | 5.02684 | 3142/256 | 0.0 | 0.749945 | 0.25008 |
| `w8_k1_prodii2_mergeii4_fifo4096` | 25136 | 80.015429 | 50268 | 5.02684 | 3142/4096 | 0.0 | 0.749945 | 0.25008 |
| `w8_k1_prodii4_mergeii1_fifo16` | 25136 | 80.015429 | 50268 | 5.02684 | 1/16 | 0.199949 | 0.749945 | 0.25008 |
| `w8_k1_prodii4_mergeii1_fifo256` | 25136 | 80.015429 | 50268 | 5.02684 | 1/256 | 0.199949 | 0.749945 | 0.25008 |
| `w8_k1_prodii4_mergeii1_fifo4096` | 25136 | 80.015429 | 50268 | 5.02684 | 1/4096 | 0.199949 | 0.749945 | 0.25008 |
| `w8_k1_prodii4_mergeii2_fifo16` | 25136 | 80.015429 | 50268 | 5.02684 | 1/16 | 0.199949 | 0.749945 | 0.25008 |
| `w8_k1_prodii4_mergeii2_fifo256` | 25136 | 80.015429 | 50268 | 5.02684 | 1/256 | 0.199949 | 0.749945 | 0.25008 |
| `w8_k1_prodii4_mergeii2_fifo4096` | 25136 | 80.015429 | 50268 | 5.02684 | 1/4096 | 0.199949 | 0.749945 | 0.25008 |

## Assumptions

- Producer emits one W-lane logit tile after producer latency and then every producer II cycles.
- Local ranker accepts one producer tile per local ranker II and emits one candidate group after local ranker latency.
- Candidate FIFO depth is reported in local candidate groups; overflow is reported as capacity evidence, not hidden by backpressure.
- Global merge consumes one local candidate group per merge II and produces the final token rank after the last merge latency.
- Buffered baseline waits for the producer to materialize all logits before rank reduction starts.
- Traffic model counts materialized-logit write+read bytes versus candidate FIFO write+read bytes.
- Measured row-8 datapath and row-16/row-32 scale critical_path_ns values are used as ranker clock proxies.
- Measured candidate-stream merge/FIFO PPA is used for global merge buffering when an exact or nearest-depth point is available.
- Memory hierarchy estimates use explicit planning parameters and are reported separately from measured cell PPA.
- Missing lane points are explicit defaults or log2-lane scaled proxies.
- Perf-sim and future RTL equivalence is defined at accepted ready-valid stream beats, FIFO occupancy, valid masks, last-beat completion, and tie-breaking.

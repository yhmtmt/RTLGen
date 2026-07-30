# Score32 Exact Reduction Full-GQA8 Frontier Rerank

- decision: `score32_exact_reduction_gqa8_full_equivalence_frontier_recorded`
- score32 latency us: `13488.364723`
- score32 token/s: `74.137971543343`
- score32 total energy upper-bound mJ/token: `484.704405630618`
- score32 total energy lower-bound mJ/token: `467.191305313106`
- energy status: `conservative_upper_bound_latency_scaled_non_hbm_energy`
- source latency us: `12814.257853`
- corrected latency us: `13488.364723`
- one-group equivalence: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_equivalence_llama7b_v1_r7`
- four-group equivalence: `l2_decoder_attention_score32_exact_local16_global_tree_cluster_sram_gqa8_rotation_equivalence_llama7b_v1`

## Ranking

- best latency candidate: `physical_hbm_gqa8_kv8_service_frontier`
- best energy candidate: `physical_hbm_gqa8_kv8_service_frontier`
- best precision-safe candidate: `score32_exp_lut_schedule_wrapper_hbm_controller_replay_best`
- best precision-safe energy candidate: `die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512`
- exact energy ranking status: `provisional_pending_reducer_and_global_tree_activity_power_measurement`

## Remaining Abstractions

- Exact reduction latency is now backed by the banked finalized-tree service contract plus one-/four-group RTL equivalence, but dedicated reducer/global-tree activity energy remains unclosed.
- Full one- and four-group GQA8 equivalence closes functional composition only; full-array postroute PPA and toggle power remain unmeasured.
- HBM replay controller area, active energy, and control timing are backed by measured Nangate45 RTL PPA.
- Score32 exact-energy ranking remains provisional until reducer/global-tree activity power is measured.
- does not include vendor HBM current signoff

## Next Step

Measure reducer/global-tree activity power and full-array postroute PPA so the quality-backed score32 frontier can replace the current conservative upper-bound energy ranking with measured exact energy.

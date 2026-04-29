# Campaign Report: npu_e2e_eval_llm_practical_v1

- generated_utc: `2026-04-29T02:26:56+00:00`
- model_set_id: `llm_practical_v1`
- model_manifest: `runs/models/llm_practical_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_llm_practical_v1__l2_llm_practical_decoder_proxy_v1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_llm_practical_v1__l2_llm_practical_decoder_proxy_v1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_llm_practical_v1__l2_llm_practical_decoder_proxy_v1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_llm_practical_v1__l2_llm_practical_decoder_proxy_v1/best_point.json`
- total_rows: `36`
- ok_rows: `36`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 3 | 0.000000 | 0.0775 | 16576.5133 | 0.00001497 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| 2 | fp16_nm1 | hier_macro | 3 | 0.219317 | 0.0775 | 16576.5133 | 0.00001530 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| 3 | fp16_nm2 | flat_nomacro | 3 | 0.878079 | 0.0775 | 16576.5133 | 0.00001631 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| 4 | fp16_nm2 | hier_macro | 3 | 1.000000 | 0.0775 | 16576.5133 | 0.00001649 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.0775 | 0.00001497 | 844.5733 |
| fp16_nm2 | flat_nomacro | 0.0775 | 0.00001631 | 828.3467 |

## Scheduler Visibility Decision

- recommendation: `no_architecture_change_yet`
- rationale: Softmax occupancy is low and no wait or backpressure counters are active; the current evidence does not justify a softmax architecture change.
- max_softmax_engine_occupancy: `0.103708`
- max_softmax_backpressure_events: `0.0000`
- max_dependency_wait_ns: `0.0000`
- latency_us_per_token_range: `2.181375..3.702687`

## Scheduler / Softmax Summary

| arch_id | macro_mode | latency_us_per_token_mean | latency_us_per_softmax_mean | softmax_ops_mean | softmax_issue_count_mean | softmax_completion_count_mean | softmax_engine_occupancy_mean | softmax_backpressure_events_mean | softmax_backpressure_ns_mean | softmax_wait_on_gemm_ns_mean | softmax_wait_on_misc_compute_ns_mean | dependency_wait_ns_mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 2.785583 | 16.084889 | 4.6667 | 4.6667 | 4.6667 | 0.088639 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm1 | hier_macro | 2.785583 | 16.084889 | 4.6667 | 4.6667 | 4.6667 | 0.088639 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | flat_nomacro | 2.785583 | 16.084889 | 4.6667 | 4.6667 | 4.6667 | 0.088639 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | hier_macro | 2.785583 | 16.084889 | 4.6667 | 4.6667 | 4.6667 | 0.088639 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.0775 | 0.00001497 | 844.5733 |
| 2 | fp16_nm1 | hier_macro | 0.0775 | 0.00001530 | 976.8733 |
| 3 | fp16_nm2 | flat_nomacro | 0.0775 | 0.00001631 | 828.3467 |
| 4 | fp16_nm2 | hier_macro | 0.0775 | 0.00001649 | 984.3200 |

## Per-Model Summary

| arch_id | macro_mode | model_id | seq_len | attn_blocks | n | latency_mean_ms | latency_us_per_token | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | practical_tail_attn4_s16_h64_kv256 | 16 | 4 | 3 | 0.0349 | 2.181375 | 0.0000 | 28651.6532 | 0.00000674 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | practical_tail_attn4_s16_h64_kv256 | 16 | 4 | 3 | 0.0349 | 2.181375 | 0.0000 | 28651.6532 | 0.00000689 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | practical_tail_attn4_s16_h64_kv256 | 16 | 4 | 3 | 0.0349 | 2.181375 | 0.0000 | 28651.6532 | 0.00000734 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | practical_tail_attn4_s16_h64_kv256 | 16 | 4 | 3 | 0.0349 | 2.181375 | 0.0000 | 28651.6532 | 0.00000743 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |
| fp16_nm1 | flat_nomacro | practical_tail_attn4_s32_h64_kv512 | 32 | 4 | 3 | 0.0791 | 2.472688 | 0.0000 | 12638.0709 | 0.00001528 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | practical_tail_attn4_s32_h64_kv512 | 32 | 4 | 3 | 0.0791 | 2.472688 | 0.0000 | 12638.0709 | 0.00001562 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | practical_tail_attn4_s32_h64_kv512 | 32 | 4 | 3 | 0.0791 | 2.472688 | 0.0000 | 12638.0709 | 0.00001665 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | practical_tail_attn4_s32_h64_kv512 | 32 | 4 | 3 | 0.0791 | 2.472688 | 0.0000 | 12638.0709 | 0.00001684 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |
| fp16_nm1 | flat_nomacro | practical_tail_attn6_s32_h64_kv512 | 32 | 6 | 3 | 0.1185 | 3.702687 | 0.0000 | 8439.8157 | 0.00002288 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | practical_tail_attn6_s32_h64_kv512 | 32 | 6 | 3 | 0.1185 | 3.702687 | 0.0000 | 8439.8157 | 0.00002339 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | practical_tail_attn6_s32_h64_kv512 | 32 | 6 | 3 | 0.1185 | 3.702687 | 0.0000 | 8439.8157 | 0.00002493 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | practical_tail_attn6_s32_h64_kv512 | 32 | 6 | 3 | 0.1185 | 3.702687 | 0.0000 | 8439.8157 | 0.00002522 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |

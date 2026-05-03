# Campaign Report: npu_e2e_eval_llm_practical_scale_v1

- generated_utc: `2026-05-03T14:15:11+00:00`
- model_set_id: `llm_practical_scale_v1`
- model_manifest: `runs/models/llm_practical_scale_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_llm_practical_scale_v1__l2_llm_practical_scale_v1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_llm_practical_scale_v1__l2_llm_practical_scale_v1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_llm_practical_scale_v1__l2_llm_practical_scale_v1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_llm_practical_scale_v1__l2_llm_practical_scale_v1/best_point.json`
- total_rows: `24`
- ok_rows: `24`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 3 | 0.000000 | 0.4387 | 2458.7883 | 0.00008473 | 5.5570 | 2250000.0000 | 0.193122 | 840.3450 | 419.4400 |
| 2 | fp16_nm1 | hier_macro | 3 | 0.219317 | 0.4387 | 2458.7883 | 0.00008662 | 5.7749 | 2250000.0000 | 0.197441 | 975.8300 | 477.8150 |
| 3 | fp16_nm2 | flat_nomacro | 3 | 0.878079 | 0.4387 | 2458.7883 | 0.00009231 | 5.7013 | 2250000.0000 | 0.210414 | 825.2900 | 414.2100 |
| 4 | fp16_nm2 | hier_macro | 3 | 1.000000 | 0.4387 | 2458.7883 | 0.00009337 | 5.7409 | 2250000.0000 | 0.212815 | 988.1350 | 459.8700 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.4387 | 0.00008473 | 840.3450 |
| fp16_nm2 | flat_nomacro | 0.4387 | 0.00009231 | 825.2900 |

## Scheduler Visibility Decision

- recommendation: `no_architecture_change_yet`
- rationale: Softmax occupancy is low and no wait or backpressure counters are active; the current evidence does not justify a softmax architecture change.
- max_softmax_engine_occupancy: `0.163398`
- max_softmax_backpressure_events: `0.0000`
- max_dependency_wait_ns: `0.0000`
- latency_us_per_token_range: `..`

## Scheduler / Softmax Summary

| arch_id | macro_mode | latency_us_per_token_mean | latency_us_per_softmax_mean | softmax_ops_mean | softmax_issue_count_mean | softmax_completion_count_mean | softmax_engine_occupancy_mean | softmax_backpressure_events_mean | softmax_backpressure_ns_mean | softmax_wait_on_gemm_ns_mean | softmax_wait_on_misc_compute_ns_mean | dependency_wait_ns_mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro |  | 67.450472 | 6.6667 | 6.6667 | 6.6667 | 0.161466 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm1 | hier_macro |  | 67.450472 | 6.6667 | 6.6667 | 6.6667 | 0.161466 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | flat_nomacro |  | 67.450472 | 6.6667 | 6.6667 | 6.6667 | 0.161466 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | hier_macro |  | 67.450472 | 6.6667 | 6.6667 | 6.6667 | 0.161466 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.4387 | 0.00008473 | 840.3450 |
| 2 | fp16_nm1 | hier_macro | 0.4387 | 0.00008662 | 975.8300 |
| 3 | fp16_nm2 | flat_nomacro | 0.4387 | 0.00009231 | 825.2900 |
| 4 | fp16_nm2 | hier_macro | 0.4387 | 0.00009337 | 988.1350 |

## Per-Model Summary

| arch_id | macro_mode | model_id | seq_len | attn_blocks | n | latency_mean_ms | latency_us_per_token | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | practical_scale_attn6_s64_h64_kv1024 |  |  | 2 | 0.3063 |  | 0.0000 | 3264.4960 | 0.00005916 | 5.5570 | 2250000.0000 | 0.193122 | 840.3450 | 419.4400 |
| fp16_nm1 | hier_macro | practical_scale_attn6_s64_h64_kv1024 |  |  | 2 | 0.3063 |  | 0.0000 | 3264.4960 | 0.00006048 | 5.7749 | 2250000.0000 | 0.197441 | 975.8300 | 477.8150 |
| fp16_nm2 | flat_nomacro | practical_scale_attn6_s64_h64_kv1024 |  |  | 2 | 0.3063 |  | 0.0000 | 3264.4960 | 0.00006446 | 5.7013 | 2250000.0000 | 0.210414 | 825.2900 | 414.2100 |
| fp16_nm2 | hier_macro | practical_scale_attn6_s64_h64_kv1024 |  |  | 2 | 0.3063 |  | 0.0000 | 3264.4960 | 0.00006519 | 5.7409 | 2250000.0000 | 0.212815 | 988.1350 | 459.8700 |
| fp16_nm1 | flat_nomacro | practical_scale_attn6_s64_h64_kv2048 |  |  | 2 | 0.6016 |  | 0.0000 | 1662.1733 | 0.00011619 | 5.5570 | 2250000.0000 | 0.193122 | 840.3450 | 419.4400 |
| fp16_nm1 | hier_macro | practical_scale_attn6_s64_h64_kv2048 |  |  | 2 | 0.6016 |  | 0.0000 | 1662.1733 | 0.00011878 | 5.7749 | 2250000.0000 | 0.197441 | 975.8300 | 477.8150 |
| fp16_nm2 | flat_nomacro | practical_scale_attn6_s64_h64_kv2048 |  |  | 2 | 0.6016 |  | 0.0000 | 1662.1733 | 0.00012659 | 5.7013 | 2250000.0000 | 0.210414 | 825.2900 | 414.2100 |
| fp16_nm2 | hier_macro | practical_scale_attn6_s64_h64_kv2048 |  |  | 2 | 0.6016 |  | 0.0000 | 1662.1733 | 0.00012803 | 5.7409 | 2250000.0000 | 0.212815 | 988.1350 | 459.8700 |
| fp16_nm1 | flat_nomacro | practical_scale_attn8_s64_h64_kv1024 |  |  | 2 | 0.4082 |  | 0.0000 | 2449.6955 | 0.00007884 | 5.5570 | 2250000.0000 | 0.193122 | 840.3450 | 419.4400 |
| fp16_nm1 | hier_macro | practical_scale_attn8_s64_h64_kv1024 |  |  | 2 | 0.4082 |  | 0.0000 | 2449.6955 | 0.00008060 | 5.7749 | 2250000.0000 | 0.197441 | 975.8300 | 477.8150 |
| fp16_nm2 | flat_nomacro | practical_scale_attn8_s64_h64_kv1024 |  |  | 2 | 0.4082 |  | 0.0000 | 2449.6955 | 0.00008589 | 5.7013 | 2250000.0000 | 0.210414 | 825.2900 | 414.2100 |
| fp16_nm2 | hier_macro | practical_scale_attn8_s64_h64_kv1024 |  |  | 2 | 0.4082 |  | 0.0000 | 2449.6955 | 0.00008687 | 5.7409 | 2250000.0000 | 0.212815 | 988.1350 | 459.8700 |

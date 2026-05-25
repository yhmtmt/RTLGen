# Campaign Report: npu_compute_full_path_guard_v1

- generated_utc: `2026-05-25T09:17:33+00:00`
- model_set_id: `mlp_smoke_v0`
- model_manifest: `runs/models/mlp_smoke_v0/manifest.json`
- results_csv: `runs/campaigns/npu/frontier_guard/compute_full_path_guard_v1__l2_npu_compute_full_path_equivalence_guard_v1/results.csv`
- summary_csv: `runs/campaigns/npu/frontier_guard/compute_full_path_guard_v1__l2_npu_compute_full_path_equivalence_guard_v1/summary.csv`
- pareto_csv: `runs/campaigns/npu/frontier_guard/compute_full_path_guard_v1__l2_npu_compute_full_path_equivalence_guard_v1/pareto.csv`
- best_json: `runs/campaigns/npu/frontier_guard/compute_full_path_guard_v1__l2_npu_compute_full_path_equivalence_guard_v1/best_point.json`
- total_rows: `2`
- ok_rows: `2`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1_guard | flat_nomacro | 1 | 0.000000 | 0.0043 | 233535.7310 | 0.00000083 | 5.5570 | 2250000.0000 | 0.193122 | 834.9900 | 416.7800 |
| 2 | fp16_nm1_guard | hier_macro | 1 | 1.000000 | 0.0043 | 233535.7310 | 0.00000085 | 5.7749 | 2250000.0000 | 0.197441 | 974.5800 | 477.8000 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1_guard | flat_nomacro | 0.0043 | 0.00000083 | 834.9900 |

## Scheduler Visibility Decision

- recommendation: `no_architecture_change_yet`
- rationale: Softmax occupancy is low and no wait or backpressure counters are active; the current evidence does not justify a softmax architecture change.
- max_softmax_engine_occupancy: `0.000000`
- max_softmax_backpressure_events: `0.0000`
- max_dependency_wait_ns: `0.0000`
- latency_us_per_token_range: `..`

## Scheduler / Softmax Summary

| arch_id | macro_mode | latency_us_per_token_mean | latency_us_per_softmax_mean | softmax_ops_mean | softmax_issue_count_mean | softmax_completion_count_mean | softmax_engine_occupancy_mean | softmax_backpressure_events_mean | softmax_backpressure_ns_mean | softmax_wait_on_gemm_ns_mean | softmax_wait_on_misc_compute_ns_mean | dependency_wait_ns_mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1_guard | flat_nomacro |  |  | 0.0000 | 0.0000 | 0.0000 | 0.000000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm1_guard | hier_macro |  |  | 0.0000 | 0.0000 | 0.0000 | 0.000000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1_guard | flat_nomacro | 0.0043 | 0.00000083 | 834.9900 |
| 2 | fp16_nm1_guard | hier_macro | 0.0043 | 0.00000085 | 974.5800 |

## Per-Model Summary

| arch_id | macro_mode | model_id | seq_len | attn_blocks | n | latency_mean_ms | latency_us_per_token | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1_guard | flat_nomacro | mlp1 |  |  | 1 | 0.0043 |  | 0.0000 | 233535.7310 | 0.00000083 | 5.5570 | 2250000.0000 | 0.193122 | 834.9900 | 416.7800 |
| fp16_nm1_guard | hier_macro | mlp1 |  |  | 1 | 0.0043 |  | 0.0000 | 233535.7310 | 0.00000085 | 5.7749 | 2250000.0000 | 0.197441 | 974.5800 | 477.8000 |

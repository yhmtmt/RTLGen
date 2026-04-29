# Campaign Report: npu_e2e_eval_mlp_smoke_v1_reuse

- generated_utc: `2026-04-29T08:28:51+00:00`
- model_set_id: `mlp_smoke_v1`
- model_manifest: `runs/models/mlp_smoke_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_q8_normalization_frontier_v1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_q8_normalization_frontier_v1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_q8_normalization_frontier_v1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_q8_normalization_frontier_v1/best_point.json`
- total_rows: `40`
- ok_rows: `40`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 2 | 0.000000 | 0.0289 | 126107.7243 | 0.00000558 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| 2 | fp16_nm1 | hier_macro | 2 | 0.027827 | 0.0289 | 126107.7243 | 0.00000571 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| 3 | fp16_nm2 | flat_nomacro | 2 | 1.974680 | 0.0473 | 73940.0697 | 0.00000996 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| 4 | fp16_nm2 | hier_macro | 2 | 2.000000 | 0.0473 | 73940.0697 | 0.00001007 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.0289 | 0.00000558 | 848.4180 |
| fp16_nm2 | flat_nomacro | 0.0473 | 0.00000996 | 829.8140 |

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
| fp16_nm1 | flat_nomacro |  |  | 0.0000 | 0.0000 | 0.0000 | 0.000000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm1 | hier_macro |  |  | 0.0000 | 0.0000 | 0.0000 | 0.000000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | flat_nomacro |  |  | 0.0000 | 0.0000 | 0.0000 | 0.000000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | hier_macro |  |  | 0.0000 | 0.0000 | 0.0000 | 0.000000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.0289 | 0.00000558 | 848.4180 |
| 2 | fp16_nm1 | hier_macro | 0.0289 | 0.00000571 | 978.8940 |
| 3 | fp16_nm2 | flat_nomacro | 0.0473 | 0.00000996 | 829.8140 |
| 4 | fp16_nm2 | hier_macro | 0.0473 | 0.00001007 | 981.7820 |

## Per-Model Summary

| arch_id | macro_mode | model_id | seq_len | attn_blocks | n | latency_mean_ms | latency_us_per_token | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | mlp1 |  |  | 5 | 0.0043 |  | 0.0000 | 233535.7310 | 0.00000083 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp1 |  |  | 5 | 0.0043 |  | 0.0000 | 233535.7310 | 0.00000085 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp1 |  |  | 5 | 0.0073 |  | 0.0000 | 136425.6480 | 0.00000154 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp1 |  |  | 5 | 0.0073 |  | 0.0000 | 136425.6480 | 0.00000156 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| fp16_nm1 | flat_nomacro | mlp2 |  |  | 5 | 0.0535 |  | 0.0000 | 18679.7176 | 0.00001034 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp2 |  |  | 5 | 0.0535 |  | 0.0000 | 18679.7176 | 0.00001057 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp2 |  |  | 5 | 0.0873 |  | 0.0000 | 11454.4913 | 0.00001837 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp2 |  |  | 5 | 0.0873 |  | 0.0000 | 11454.4913 | 0.00001858 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

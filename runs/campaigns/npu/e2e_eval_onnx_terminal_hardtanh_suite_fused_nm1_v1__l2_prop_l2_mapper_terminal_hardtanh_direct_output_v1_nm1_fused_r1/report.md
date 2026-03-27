# Campaign Report: npu_e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1

- generated_utc: `2026-03-27T02:54:39+00:00`
- model_set_id: `onnx_terminal_hardtanh_suite_v1`
- model_manifest: `runs/models/onnx_terminal_hardtanh_suite_v1/manifest.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_fused_r1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_fused_r1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_fused_r1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_terminal_hardtanh_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_hardtanh_direct_output_v1_nm1_fused_r1/best_point.json`
- total_rows: `3`
- ok_rows: `3`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1_hardtanhproxy | hier_macro | 3 | 0.000000 | 0.0053 | 422212.7994 | 0.00000000 | 2.7883 | 1440000.0000 | 0.000360 | 59.4400 |  |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1_hardtanhproxy | hier_macro | 0.0053 | 0.00000000 | 59.4400 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1_hardtanhproxy | hier_macro | 0.0053 | 0.00000000 | 59.4400 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1_hardtanhproxy | hier_macro | hardtanh_vec_b128_f64 | 1 | 0.0017 | 0.0000 | 593119.8102 | 0.00000000 | 2.7883 | 1440000.0000 | 0.000360 | 59.4400 |  |
| fp16_nm1_hardtanhproxy | hier_macro | hardtanh_vec_b256_f256 | 1 | 0.0124 | 0.0000 | 80398.7779 | 0.00000000 | 2.7883 | 1440000.0000 | 0.000360 | 59.4400 |  |
| fp16_nm1_hardtanhproxy | hier_macro | hardtanh_vec_flatten_b128_2x4x8 | 1 | 0.0017 | 0.0000 | 593119.8102 | 0.00000000 | 2.7883 | 1440000.0000 | 0.000360 | 59.4400 |  |

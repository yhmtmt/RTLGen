# Campaign Report: npu_e2e_eval_onnx_imported_softmax_tail_num_modules_v1

- generated_utc: `2026-04-15T13:46:22+00:00`
- model_set_id: `onnx_imported_softmax_tail_v1`
- model_manifest: `runs/models/onnx_imported_softmax_tail_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1__l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1__l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1__l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1__l2_prop_l2_num_modules_adaptive_v1_nm1_nm2_r1/best_point.json`
- total_rows: `20`
- ok_rows: `20`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 1 | 0.000000 | 0.0010 | 1033324.7223 | 0.00000019 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| 2 | fp16_nm1 | hier_macro | 1 | 0.219317 | 0.0010 | 1033324.7223 | 0.00000019 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| 3 | fp16_nm2 | flat_nomacro | 1 | 0.878079 | 0.0010 | 1033324.7223 | 0.00000020 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| 4 | fp16_nm2 | hier_macro | 1 | 1.000000 | 0.0010 | 1033324.7223 | 0.00000021 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.0010 | 0.00000019 | 848.4180 |
| fp16_nm2 | flat_nomacro | 0.0010 | 0.00000020 | 829.8140 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.0010 | 0.00000019 | 848.4180 |
| 2 | fp16_nm1 | hier_macro | 0.0010 | 0.00000019 | 978.8940 |
| 3 | fp16_nm2 | flat_nomacro | 0.0010 | 0.00000020 | 829.8140 |
| 4 | fp16_nm2 | hier_macro | 0.0010 | 0.00000021 | 981.7820 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | logistic_regression | 5 | 0.0010 | 0.0000 | 1033324.7223 | 0.00000019 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | logistic_regression | 5 | 0.0010 | 0.0000 | 1033324.7223 | 0.00000019 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | logistic_regression | 5 | 0.0010 | 0.0000 | 1033324.7223 | 0.00000020 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | logistic_regression | 5 | 0.0010 | 0.0000 | 1033324.7223 | 0.00000021 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

# Campaign Report: npu_e2e_eval_onnx_imported_mlp_num_modules_v1

- generated_utc: `2026-03-06T08:45:55+00:00`
- model_set_id: `onnx_imported_mlp_v1`
- model_manifest: `runs/models/onnx_imported_mlp_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_mlp_num_modules_v1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_mlp_num_modules_v1/objective_profiles/latency/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_mlp_num_modules_v1/objective_profiles/latency/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_imported_mlp_num_modules_v1/objective_profiles/latency/best_point.json`
- total_rows: `40`
- ok_rows: `40`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=0.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm2 | flat_nomacro | 2 | 0.000000 | 0.0428 | 63417.1469 | 0.00000901 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| 2 | fp16_nm2 | hier_macro | 2 | 0.000000 | 0.0428 | 63417.1469 | 0.00000912 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| 3 | fp16_nm1 | flat_nomacro | 2 | 1.000000 | 0.0480 | 54958.3502 | 0.00000927 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| 4 | fp16_nm1 | hier_macro | 2 | 1.000000 | 0.0480 | 54958.3502 | 0.00000948 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm2 | flat_nomacro | 0.0428 | 0.00000901 | 829.8140 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm2 | flat_nomacro | 0.0428 | 0.00000901 | 829.8140 |
| 2 | fp16_nm2 | hier_macro | 0.0428 | 0.00000912 | 981.7820 |
| 3 | fp16_nm1 | flat_nomacro | 0.0480 | 0.00000927 | 848.4180 |
| 4 | fp16_nm1 | hier_macro | 0.0480 | 0.00000948 | 978.8940 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | armor_mlp | 5 | 0.0102 | 0.0000 | 98264.4049 | 0.00000197 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | armor_mlp | 5 | 0.0102 | 0.0000 | 98264.4049 | 0.00000201 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | armor_mlp | 5 | 0.0088 | 0.0000 | 113830.3927 | 0.00000185 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | armor_mlp | 5 | 0.0088 | 0.0000 | 113830.3927 | 0.00000187 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| fp16_nm1 | flat_nomacro | mnist_mlp | 5 | 0.0858 | 0.0000 | 11652.2955 | 0.00001657 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mnist_mlp | 5 | 0.0858 | 0.0000 | 11652.2955 | 0.00001694 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mnist_mlp | 5 | 0.0769 | 0.0000 | 13003.9012 | 0.00001618 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mnist_mlp | 5 | 0.0769 | 0.0000 | 13003.9012 | 0.00001637 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

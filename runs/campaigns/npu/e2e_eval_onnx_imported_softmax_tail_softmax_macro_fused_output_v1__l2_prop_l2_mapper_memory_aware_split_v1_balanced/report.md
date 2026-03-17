# Campaign Report: npu_e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1

- generated_utc: `2026-03-17T12:06:38+00:00`
- model_set_id: `onnx_imported_softmax_tail_v1`
- model_manifest: `runs/models/onnx_imported_softmax_tail_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign__l2_prop_l2_mapper_memory_aware_split_v1_balanced.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_mapper_memory_aware_split_v1_balanced/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_mapper_memory_aware_split_v1_balanced/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_mapper_memory_aware_split_v1_balanced/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1__l2_prop_l2_mapper_memory_aware_split_v1_balanced/best_point.json`
- total_rows: `12`
- ok_rows: `12`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1_softmax_r4 | flat_nomacro | 1 | 0.000000 | 0.0006 | 1610305.9581 | 0.00000011 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| 2 | fp16_nm2_softmax_r4 | flat_nomacro | 1 | 0.248229 | 0.0006 | 1610305.9581 | 0.00000012 | 5.4768 | 2250000.0000 | 0.189074 | 1194.5267 | 566.2600 |
| 3 | fp16_nm2_softmax_r4 | hier_macro | 1 | 0.790726 | 0.0006 | 1610305.9581 | 0.00000012 | 5.6781 | 2250000.0000 | 0.198878 | 1233.9233 | 551.5533 |
| 4 | fp16_nm1_softmax_r4 | hier_macro | 1 | 1.000000 | 0.0006 | 1610305.9581 | 0.00000013 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1_softmax_r4 | flat_nomacro | 0.0006 | 0.00000011 | 1318.7400 |
| fp16_nm2_softmax_r4 | flat_nomacro | 0.0006 | 0.00000012 | 1194.5267 |
| fp16_nm1_softmax_r4 | hier_macro | 0.0006 | 0.00000013 | 1146.6100 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1_softmax_r4 | flat_nomacro | 0.0006 | 0.00000011 | 1318.7400 |
| 2 | fp16_nm2_softmax_r4 | flat_nomacro | 0.0006 | 0.00000012 | 1194.5267 |
| 3 | fp16_nm2_softmax_r4 | hier_macro | 0.0006 | 0.00000012 | 1233.9233 |
| 4 | fp16_nm1_softmax_r4 | hier_macro | 0.0006 | 0.00000013 | 1146.6100 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1_softmax_r4 | flat_nomacro | logistic_regression | 3 | 0.0006 | 0.0000 | 1610305.9581 | 0.00000011 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | logistic_regression | 3 | 0.0006 | 0.0000 | 1610305.9581 | 0.00000013 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |
| fp16_nm2_softmax_r4 | flat_nomacro | logistic_regression | 3 | 0.0006 | 0.0000 | 1610305.9581 | 0.00000012 | 5.4768 | 2250000.0000 | 0.189074 | 1194.5267 | 566.2600 |
| fp16_nm2_softmax_r4 | hier_macro | logistic_regression | 3 | 0.0006 | 0.0000 | 1610305.9581 | 0.00000012 | 5.6781 | 2250000.0000 | 0.198878 | 1233.9233 | 551.5533 |

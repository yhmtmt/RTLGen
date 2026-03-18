# Campaign Report: npu_e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1

- generated_utc: `2026-03-18T11:49:30+00:00`
- model_set_id: `onnx_terminal_softmax_suite_v1`
- model_manifest: `runs/models/onnx_terminal_softmax_suite_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/best_point.json`
- total_rows: `18`
- ok_rows: `18`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1_softmax_r4 | flat_nomacro | 3 | 0.000000 | 0.0037 | 419229.1094 | 0.00000067 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| 2 | fp16_nm1_softmax_r4 | hier_macro | 3 | 1.000000 | 0.0037 | 419229.1094 | 0.00000074 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1_softmax_r4 | flat_nomacro | 0.0037 | 0.00000067 | 1318.7400 |
| fp16_nm1_softmax_r4 | hier_macro | 0.0037 | 0.00000074 | 1146.6100 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1_softmax_r4 | flat_nomacro | 0.0037 | 0.00000067 | 1318.7400 |
| 2 | fp16_nm1_softmax_r4 | hier_macro | 0.0037 | 0.00000074 | 1146.6100 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1_softmax_r4 | flat_nomacro | softmax_cls_b128_i4_o128 | 3 | 0.0047 | 0.0000 | 210703.7505 | 0.00000088 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | softmax_cls_b128_i4_o128 | 3 | 0.0047 | 0.0000 | 210703.7505 | 0.00000096 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |
| fp16_nm1_softmax_r4 | flat_nomacro | softmax_cls_b128_i8_o16 | 3 | 0.0012 | 0.0000 | 848176.4207 | 0.00000022 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | softmax_cls_b128_i8_o16 | 3 | 0.0012 | 0.0000 | 848176.4207 | 0.00000024 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |
| fp16_nm1_softmax_r4 | flat_nomacro | softmax_cls_b256_i8_o64 | 3 | 0.0050 | 0.0000 | 198807.1571 | 0.00000093 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | softmax_cls_b256_i8_o64 | 3 | 0.0050 | 0.0000 | 198807.1571 | 0.00000102 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |

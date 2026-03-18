# Campaign Report: npu_e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1

- generated_utc: `2026-03-18T11:39:18+00:00`
- model_set_id: `onnx_terminal_softmax_suite_v1`
- model_manifest: `runs/models/onnx_terminal_softmax_suite_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/best_point.json`
- total_rows: `18`
- ok_rows: `18`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1_softmax_r4 | flat_nomacro | 3 | 0.000000 | 0.0045 | 347861.9143 | 0.00000083 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| 2 | fp16_nm1_softmax_r4 | hier_macro | 3 | 1.000000 | 0.0045 | 347861.9143 | 0.00000091 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1_softmax_r4 | flat_nomacro | 0.0045 | 0.00000083 | 1318.7400 |
| fp16_nm1_softmax_r4 | hier_macro | 0.0045 | 0.00000091 | 1146.6100 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1_softmax_r4 | flat_nomacro | 0.0045 | 0.00000083 | 1318.7400 |
| 2 | fp16_nm1_softmax_r4 | hier_macro | 0.0045 | 0.00000091 | 1146.6100 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1_softmax_r4 | flat_nomacro | softmax_cls_b128_i4_o128 | 3 | 0.0059 | 0.0000 | 170357.7513 | 0.00000108 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | softmax_cls_b128_i4_o128 | 3 | 0.0059 | 0.0000 | 170357.7513 | 0.00000119 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |
| fp16_nm1_softmax_r4 | flat_nomacro | softmax_cls_b128_i8_o16 | 3 | 0.0014 | 0.0000 | 710732.0540 | 0.00000026 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | softmax_cls_b128_i8_o16 | 3 | 0.0014 | 0.0000 | 710732.0540 | 0.00000029 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |
| fp16_nm1_softmax_r4 | flat_nomacro | softmax_cls_b256_i8_o64 | 3 | 0.0062 | 0.0000 | 162495.9376 | 0.00000114 | 5.6903 | 2250000.0000 | 0.184588 | 1318.7400 | 795.3067 |
| fp16_nm1_softmax_r4 | hier_macro | softmax_cls_b256_i8_o64 | 3 | 0.0062 | 0.0000 | 162495.9376 | 0.00000125 | 5.6017 | 2250000.0000 | 0.202660 | 1146.6100 | 492.9033 |

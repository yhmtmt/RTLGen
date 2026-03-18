# Campaign Report: npu_e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1

- generated_utc: `2026-03-18T12:46:19+00:00`
- model_set_id: `onnx_terminal_direct_output_suite_v1`
- model_manifest: `runs/models/onnx_terminal_direct_output_suite_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1/best_point.json`
- total_rows: `18`
- ok_rows: `18`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 3 | 0.000000 | 0.0045 | 277929.7456 | 0.00000086 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| 2 | fp16_nm1 | hier_macro | 3 | 1.000000 | 0.0045 | 277929.7456 | 0.00000088 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.0045 | 0.00000086 | 844.5733 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.0045 | 0.00000086 | 844.5733 |
| 2 | fp16_nm1 | hier_macro | 0.0045 | 0.00000088 | 976.8733 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | linear_tail_b128_f8_o64 | 3 | 0.0023 | 0.0000 | 438981.5628 | 0.00000044 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | linear_tail_b128_f8_o64 | 3 | 0.0023 | 0.0000 | 438981.5628 | 0.00000045 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm1 | flat_nomacro | linear_tail_b256_f8_o128 | 3 | 0.0072 | 0.0000 | 139314.5723 | 0.00000139 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | linear_tail_b256_f8_o128 | 3 | 0.0072 | 0.0000 | 139314.5723 | 0.00000142 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm1 | flat_nomacro | relu_tail_b128_f8_o128 | 3 | 0.0039 | 0.0000 | 255493.1017 | 0.00000076 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | relu_tail_b128_f8_o128 | 3 | 0.0039 | 0.0000 | 255493.1017 | 0.00000077 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |

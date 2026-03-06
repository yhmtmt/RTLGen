# Campaign Report: npu_e2e_eval_onnx_practical_v1_reuse_num_modules_v1

- generated_utc: `2026-03-06T07:46:51+00:00`
- model_set_id: `onnx_practical_v1`
- model_manifest: `runs/models/onnx_practical_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/objective_profiles/ppa/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/objective_profiles/ppa/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/objective_profiles/ppa/best_point.json`
- total_rows: `60`
- ok_rows: `60`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.25, power=0.25, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 3 | 1.000000 | 0.8796 | 1450.3448 | 0.00016987 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| 2 | fp16_nm2 | flat_nomacro | 3 | 1.050849 | 0.8554 | 1485.6093 | 0.00017999 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| 3 | fp16_nm2 | hier_macro | 3 | 1.250000 | 0.8554 | 1485.6093 | 0.00018204 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| 4 | fp16_nm1 | hier_macro | 3 | 1.366815 | 0.8796 | 1450.3448 | 0.00017366 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm2 | flat_nomacro | 0.8554 | 0.00017999 | 829.8140 |
| fp16_nm1 | flat_nomacro | 0.8796 | 0.00016987 | 848.4180 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm2 | flat_nomacro | 0.8554 | 0.00017999 | 829.8140 |
| 2 | fp16_nm2 | hier_macro | 0.8554 | 0.00018204 | 981.7820 |
| 3 | fp16_nm1 | flat_nomacro | 0.8796 | 0.00016987 | 848.4180 |
| 4 | fp16_nm1 | hier_macro | 0.8796 | 0.00017366 | 978.8940 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | mlp_p1 | 5 | 0.4160 | 0.0000 | 2403.5919 | 0.00008035 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp_p1 | 5 | 0.4160 | 0.0000 | 2403.5919 | 0.00008214 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp_p1 | 5 | 0.4051 | 0.0000 | 2468.3435 | 0.00008525 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp_p1 | 5 | 0.4051 | 0.0000 | 2468.3435 | 0.00008622 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| fp16_nm1 | flat_nomacro | mlp_p2 | 5 | 1.4175 | 0.0000 | 705.4594 | 0.00027375 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp_p2 | 5 | 1.4175 | 0.0000 | 705.4594 | 0.00027988 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp_p2 | 5 | 1.3647 | 0.0000 | 732.7521 | 0.00028716 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp_p2 | 5 | 1.3647 | 0.0000 | 732.7521 | 0.00029043 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| fp16_nm1 | flat_nomacro | mlp_p3 | 5 | 0.8052 | 0.0000 | 1241.9830 | 0.00015549 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp_p3 | 5 | 0.8052 | 0.0000 | 1241.9830 | 0.00015897 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp_p3 | 5 | 0.7963 | 0.0000 | 1255.7324 | 0.00016756 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp_p3 | 5 | 0.7963 | 0.0000 | 1255.7324 | 0.00016947 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

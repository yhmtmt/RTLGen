# Campaign Report: npu_e2e_eval_v0

- generated_utc: `2026-03-03T04:54:29+00:00`
- results_csv: `runs/campaigns/npu/e2e_eval_v0/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_v0/objective_profiles/latency/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_v0/objective_profiles/latency/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_v0/objective_profiles/latency/best_point.json`
- total_rows: `40`
- ok_rows: `40`
- non_ok_rows: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=0.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 2 | 0.000000 | 0.0194 | 196851.1912 | 0.00000375 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| 2 | fp16_nm1 | hier_macro | 2 | 0.000000 | 0.0194 | 196851.1912 | 0.00000384 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| 3 | fp16_nm2 | flat_nomacro | 2 | 0.000000 | 0.0194 | 196851.1912 | 0.00000409 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| 4 | fp16_nm2 | hier_macro | 2 | 0.000000 | 0.0194 | 196851.1912 | 0.00000414 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.0194 | 0.00000375 | 848.4180 |
| fp16_nm2 | flat_nomacro | 0.0194 | 0.00000409 | 829.8140 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.0194 | 0.00000375 | 848.4180 |
| 2 | fp16_nm1 | hier_macro | 0.0194 | 0.00000384 | 978.8940 |
| 3 | fp16_nm2 | flat_nomacro | 0.0194 | 0.00000409 | 829.8140 |
| 4 | fp16_nm2 | hier_macro | 0.0194 | 0.00000414 | 981.7820 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | mlp1 | 5 | 0.0027 | 0.0000 | 366032.2108 | 0.00000053 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp1 | 5 | 0.0027 | 0.0000 | 366032.2108 | 0.00000054 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp1 | 5 | 0.0027 | 0.0000 | 366032.2108 | 0.00000057 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp1 | 5 | 0.0027 | 0.0000 | 366032.2108 | 0.00000058 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |
| fp16_nm1 | flat_nomacro | mlp2 | 5 | 0.0361 | 0.0000 | 27670.1716 | 0.00000698 | 5.5570 | 2250000.0000 | 0.193122 | 848.4180 | 424.7380 |
| fp16_nm1 | hier_macro | mlp2 | 5 | 0.0361 | 0.0000 | 27670.1716 | 0.00000714 | 5.7749 | 2250000.0000 | 0.197441 | 978.8940 | 480.1040 |
| fp16_nm2 | flat_nomacro | mlp2 | 5 | 0.0361 | 0.0000 | 27670.1716 | 0.00000760 | 5.7013 | 2250000.0000 | 0.210414 | 829.8140 | 415.6120 |
| fp16_nm2 | hier_macro | mlp2 | 5 | 0.0361 | 0.0000 | 27670.1716 | 0.00000769 | 5.7409 | 2250000.0000 | 0.212815 | 981.7820 | 452.3540 |

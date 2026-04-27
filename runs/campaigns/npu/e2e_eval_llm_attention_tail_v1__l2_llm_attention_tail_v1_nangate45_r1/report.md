# Campaign Report: npu_e2e_eval_llm_attention_tail_v1

- generated_utc: `2026-04-26T12:15:49+00:00`
- model_set_id: `llm_attention_tail_v1`
- model_manifest: `runs/models/llm_attention_tail_v1/manifest.json`
- physical_source_campaign: `runs/campaigns/npu/e2e_eval_v0/campaign.json`
- results_csv: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/results.csv`
- summary_csv: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/summary.csv`
- pareto_csv: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/pareto.csv`
- best_json: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/best_point.json`
- total_rows: `60`
- ok_rows: `60`
- non_ok_rows: `0`
- duplicate_sample_rows_dropped: `0`

## Objective Ranking (weighted normalized minimization)

- weights: `latency=1.0, energy=1.0, area=0.0, power=0.0, runtime=0.0`

| rank | arch_id | macro_mode | model_count | objective_score | latency_ms_mean | throughput_mean | energy_mj_mean | critical_path_ns_mean | die_area_um2_mean | total_power_mw_mean | flow_elapsed_s_mean | place_gp_elapsed_s_mean |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 5 | 0.000000 | 0.0199 | 85743.7332 | 0.00000384 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| 2 | fp16_nm1 | hier_macro | 5 | 0.219317 | 0.0199 | 85743.7332 | 0.00000393 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| 3 | fp16_nm2 | flat_nomacro | 5 | 0.878079 | 0.0199 | 85743.7332 | 0.00000418 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| 4 | fp16_nm2 | hier_macro | 5 | 1.000000 | 0.0199 | 85743.7332 | 0.00000423 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |

## Pareto Set (latency, energy, flow runtime)

| arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---|---|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 0.0199 | 0.00000384 | 844.5733 |
| fp16_nm2 | flat_nomacro | 0.0199 | 0.00000418 | 828.3467 |

## Scheduler / Softmax Summary

| arch_id | macro_mode | softmax_ops_mean | softmax_issue_count_mean | softmax_completion_count_mean | softmax_engine_occupancy_mean | softmax_backpressure_events_mean | softmax_backpressure_ns_mean | softmax_wait_on_gemm_ns_mean | softmax_wait_on_misc_compute_ns_mean | dependency_wait_ns_mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 3.0000 | 3.0000 | 3.0000 | 0.104260 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm1 | hier_macro | 3.0000 | 3.0000 | 3.0000 | 0.104260 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | flat_nomacro | 3.0000 | 3.0000 | 3.0000 | 0.104260 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fp16_nm2 | hier_macro | 3.0000 | 3.0000 | 3.0000 | 0.104260 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Lexicographic Ranking (legacy)

| rank | arch_id | macro_mode | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean |
|---:|---|---|---:|---:|---:|
| 1 | fp16_nm1 | flat_nomacro | 0.0199 | 0.00000384 | 844.5733 |
| 2 | fp16_nm1 | hier_macro | 0.0199 | 0.00000393 | 976.8733 |
| 3 | fp16_nm2 | flat_nomacro | 0.0199 | 0.00000418 | 828.3467 |
| 4 | fp16_nm2 | hier_macro | 0.0199 | 0.00000423 | 984.3200 |

## Per-Model Summary

| arch_id | macro_mode | model_id | n | latency_mean_ms | latency_std_ms | throughput_mean | energy_mean_mj | cp_mean_ns | area_mean_um2 | power_mean_mw | flow_mean_s | place_gp_mean_s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | tail_attn2_s32_h64 | 3 | 0.0051 | 0.0000 | 194325.6899 | 0.00000099 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | tail_attn2_s32_h64 | 3 | 0.0051 | 0.0000 | 194325.6899 | 0.00000102 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | tail_attn2_s32_h64 | 3 | 0.0051 | 0.0000 | 194325.6899 | 0.00000108 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | tail_attn2_s32_h64 | 3 | 0.0051 | 0.0000 | 194325.6899 | 0.00000110 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |
| fp16_nm1 | flat_nomacro | tail_attn2_s64_h64 | 3 | 0.0103 | 0.0000 | 97370.9834 | 0.00000198 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | tail_attn2_s64_h64 | 3 | 0.0103 | 0.0000 | 97370.9834 | 0.00000203 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | tail_attn2_s64_h64 | 3 | 0.0103 | 0.0000 | 97370.9834 | 0.00000216 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | tail_attn2_s64_h64 | 3 | 0.0103 | 0.0000 | 97370.9834 | 0.00000219 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |
| fp16_nm1 | flat_nomacro | tail_attn3_s64_h64 | 3 | 0.0151 | 0.0000 | 66339.3923 | 0.00000291 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | tail_attn3_s64_h64 | 3 | 0.0151 | 0.0000 | 66339.3923 | 0.00000298 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | tail_attn3_s64_h64 | 3 | 0.0151 | 0.0000 | 66339.3923 | 0.00000317 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | tail_attn3_s64_h64 | 3 | 0.0151 | 0.0000 | 66339.3923 | 0.00000321 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |
| fp16_nm1 | flat_nomacro | tail_attn4_s128_h64 | 3 | 0.0491 | 0.0000 | 20375.7284 | 0.00000948 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | tail_attn4_s128_h64 | 3 | 0.0491 | 0.0000 | 20375.7284 | 0.00000969 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | tail_attn4_s128_h64 | 3 | 0.0491 | 0.0000 | 20375.7284 | 0.00001033 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | tail_attn4_s128_h64 | 3 | 0.0491 | 0.0000 | 20375.7284 | 0.00001044 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |
| fp16_nm1 | flat_nomacro | tail_attn4_s64_h64 | 3 | 0.0199 | 0.0000 | 50306.8719 | 0.00000384 | 5.5570 | 2250000.0000 | 0.193122 | 844.5733 | 422.0267 |
| fp16_nm1 | hier_macro | tail_attn4_s64_h64 | 3 | 0.0199 | 0.0000 | 50306.8719 | 0.00000392 | 5.7749 | 2250000.0000 | 0.197441 | 976.8733 | 478.5867 |
| fp16_nm2 | flat_nomacro | tail_attn4_s64_h64 | 3 | 0.0199 | 0.0000 | 50306.8719 | 0.00000418 | 5.7013 | 2250000.0000 | 0.210414 | 828.3467 | 416.0700 |
| fp16_nm2 | hier_macro | tail_attn4_s64_h64 | 3 | 0.0199 | 0.0000 | 50306.8719 | 0.00000423 | 5.7409 | 2250000.0000 | 0.212815 | 984.3200 | 454.9400 |

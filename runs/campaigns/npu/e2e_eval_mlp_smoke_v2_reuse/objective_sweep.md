# Objective Sweep: npu_e2e_eval_mlp_smoke_v2_reuse

- generated_utc: `2026-03-05T07:30:40+00:00`
- source_campaign: `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/campaign.json`
- output_csv: `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_sweep.csv`
- profile_artifacts_dir: `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles`

| profile | w_latency | w_energy | w_area | w_power | w_runtime | best_arch_id | best_macro_mode | objective_score | latency_ms_mean | energy_mj_mean | flow_elapsed_s_mean | report_md |
|---|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---|
| balanced | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | fp16_nm1 | flat_nomacro | 0.000000 | 0.019436 | 0.000003754 | 848.4180 | `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles/balanced/report.md` |
| latency | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | fp16_nm1 | flat_nomacro | 0.000000 | 0.019436 | 0.000003754 | 848.4180 | `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles/latency/report.md` |
| energy | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | fp16_nm1 | flat_nomacro | 0.000000 | 0.019436 | 0.000003754 | 848.4180 | `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles/energy/report.md` |
| runtime_bal | 0.500 | 0.500 | 0.000 | 0.000 | 1.000 | fp16_nm1 | flat_nomacro | 0.122421 | 0.019436 | 0.000003754 | 848.4180 | `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles/runtime_bal/report.md` |
| ppa | 1.000 | 1.000 | 0.250 | 0.250 | 0.000 | fp16_nm1 | flat_nomacro | 0.000000 | 0.019436 | 0.000003754 | 848.4180 | `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles/ppa/report.md` |

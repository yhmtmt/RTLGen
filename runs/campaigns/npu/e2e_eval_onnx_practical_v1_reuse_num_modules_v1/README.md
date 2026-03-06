# NPU E2E Evaluation Campaign: `onnx_practical_v1` Reuse `num_modules` v1

This campaign reruns the practical-scale `onnx_practical_v1` benchmark set with
architecture-aware mapper/perf artifacts so `compute.gemm.num_modules` affects
schedule lowering and analytical latency.

What it does:
- uses model-set identity `onnx_practical_v1`,
- reuses existing physical baselines through shared `synth_design_dir` data,
- regenerates mapper/perf artifacts per `(arch_id, model_id)` instead of per
  model only,
- lowers `num_modules > 1` into row-parallel GEMM descriptors and multi-engine
  perf overlap,
- records provenance via `physical_source_campaign` in result rows.

Manifest:
- `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/campaign.json \
  --check_paths
```

Run mapper+perf merge (no OpenROAD rerun expected):
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/campaign.json \
  --no_reuse_model_artifacts
```

Generate report/objective sweep:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/campaign.json

python3 npu/eval/optimize_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/campaign.json \
  --profiles_json runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/objective_profiles.json
```

Notes:
- This set still uses practical-scale MLP proxies. Replace them with imported
  production ONNX models in the next model-set revision while preserving
  explicit campaign IDs per revision.
- Under the current balanced objective, `fp16_nm2 + flat_nomacro` is the best
  point. Energy-only and broader PPA-weighted profiles still prefer
  `fp16_nm1 + flat_nomacro`.
- If architecture/PDK settings change and physical rows are missing, run with
  `--run_physical` on evaluator hardware.

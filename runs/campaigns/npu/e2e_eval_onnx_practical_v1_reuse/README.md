# NPU E2E Evaluation Campaign: `onnx_practical_v1` Reuse

This campaign is the first practical-scale benchmark-set revision beyond
smoke-only models.

What it does:
- uses model-set identity `onnx_practical_v1`,
- reuses existing physical baselines through shared `synth_design_dir` data,
- records provenance via `physical_source_campaign` in result rows.

Manifest:
- `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json \
  --check_paths
```

Run mapper+perf merge (no OpenROAD rerun expected):
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json
```

Generate report/objective sweep:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json

python3 npu/eval/optimize_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json \
  --profiles_json runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/objective_profiles.json
```

Notes:
- This set currently uses practical-scale MLP proxies. Replace with imported
  production ONNX models in the next model-set revision while preserving
  campaign ID per revision.
- If architecture/PDK settings change and physical rows are missing, run with
  `--run_physical` on evaluator hardware.

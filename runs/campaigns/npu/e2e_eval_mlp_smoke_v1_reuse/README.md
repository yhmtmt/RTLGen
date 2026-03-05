# NPU E2E Evaluation Campaign: `mlp_smoke_v1` Reuse

This campaign is the Phase-5 bootstrap for benchmark-set expansion.

What it does:
- uses a new model-set identity (`mlp_smoke_v1`),
- reuses existing physical baselines through shared `synth_design_dir` data,
- records provenance via `physical_source_campaign` in result rows.

Manifest:
- `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json`

Validate:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json \
  --check_paths
```

Run mapper+perf merge (no OpenROAD rerun expected):
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json
```

Generate report/objective sweep:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json

python3 npu/eval/optimize_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json \
  --profiles_json runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/objective_profiles.json
```

Notes:
- Replace `runs/models/mlp_smoke_v1/*` with broader ONNX benchmark models in
  later iterations; keep campaign ID distinct for each benchmark revision.
- If architecture/PDK settings change and physical rows are missing, run with
  `--run_physical` on evaluator hardware.

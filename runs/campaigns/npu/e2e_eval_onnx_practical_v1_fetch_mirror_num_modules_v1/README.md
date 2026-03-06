# NPU E2E Evaluation Campaign: `onnx_practical_v1_fetch_mirror_v1` `num_modules` v1

This campaign exercises the evaluator-side external fetch workflow with the
current practical MLP proxy set. It keeps ONNX binaries out of Git by caching
them under `runs/model_cache/` before mapper/perf execution.

What it does:
- uses model-set identity `onnx_practical_v1_fetch_mirror_v1`
- fetches cache-backed ONNX files into `runs/model_cache/`
- reuses existing physical baselines through shared `synth_design_dir` data
- regenerates mapper/perf artifacts per `(arch_id, model_id)` with corrected
  `num_modules` handling

Materialize model cache:

```sh
python3 npu/eval/fetch_models.py \
  --manifest runs/models/onnx_practical_v1_fetch_mirror_v1/manifest.json
```

Validate:

```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_fetch_mirror_num_modules_v1/campaign.json \
  --check_paths
```

Run mapper+perf merge:

```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_fetch_mirror_num_modules_v1/campaign.json \
  --no_reuse_model_artifacts
```

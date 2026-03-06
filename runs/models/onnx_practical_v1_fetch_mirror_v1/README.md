# ONNX Practical Model Set (`onnx_practical_v1_fetch_mirror_v1`)

Purpose: bootstrap evaluator-side external fetch workflow with the current
practical MLP proxy set, without tracking the ONNX binaries in Git.

What this set is:
- content-identical mirror of `onnx_practical_v1`
- binaries materialize into `runs/model_cache/onnx_practical_v1_fetch_mirror_v1/`
- fetch URLs are pinned to a GitHub raw URL at commit
  `d76a23b0fc078402a2015eb5cdb223eef670fb56`

What this set is not:
- not a broader imported production-model benchmark yet
- not a replacement for future non-MLP ONNX sets once mapper coverage expands

Materialize cache files:

```sh
python3 npu/eval/fetch_models.py \
  --manifest runs/models/onnx_practical_v1_fetch_mirror_v1/manifest.json
```

Then validate/run campaigns normally:

```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_fetch_mirror_num_modules_v1/campaign.json \
  --check_paths
```

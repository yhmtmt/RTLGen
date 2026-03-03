# NPU E2E Evaluation Campaign (v0)

This campaign skeleton is the starting point for system-level evaluation:
- map ONNX models to descriptors,
- run physical mapping for architecture points,
- run perf simulation with physical feedback,
- aggregate merged result rows.

## Manifest
- `runs/campaigns/npu/e2e_eval_v0/campaign.json`

Validate manifest:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```

Validate and check currently existing paths:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --check_paths
```

Run campaign scaffold (mapper + perf + merged rows):
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
This campaign pins physical-row selection per architecture point using
`physical_select.compare_group` and `physical_select.tag_prefix`.

Generate report and ranking:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
Outputs:
- `runs/campaigns/npu/e2e_eval_v0/report.md`
- `runs/campaigns/npu/e2e_eval_v0/summary.csv`
- `runs/campaigns/npu/e2e_eval_v0/pareto.csv`
- `runs/campaigns/npu/e2e_eval_v0/best_point.json`

## Model placeholders
The manifest references `models/mlp1.onnx` and `models/mlp2.onnx`.
Generate them with:
```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out runs/campaigns/npu/e2e_eval_v0/models/mlp1.onnx
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp2 --out runs/campaigns/npu/e2e_eval_v0/models/mlp2.onnx
```

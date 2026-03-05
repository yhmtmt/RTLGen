# MLP Smoke Model Set (`mlp_smoke_v1`)

Purpose: versioned benchmark-set revision used to launch new campaigns while
keeping model-set identity explicit in result rows.

Current content intentionally mirrors `mlp_smoke_v0` to validate the campaign
split from physical baseline reuse.

Generate or refresh ONNX files:

```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out runs/models/mlp_smoke_v1/mlp1.onnx
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp2 --out runs/models/mlp_smoke_v1/mlp2.onnx
sha256sum runs/models/mlp_smoke_v1/mlp1.onnx runs/models/mlp_smoke_v1/mlp2.onnx
```

If binaries are regenerated, update `manifest.json` hashes.

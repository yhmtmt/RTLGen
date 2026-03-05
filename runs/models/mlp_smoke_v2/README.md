# MLP Smoke Model Set (`mlp_smoke_v2`)

Purpose: next revisioned benchmark-set identity for campaign expansion while
keeping model provenance explicit in result rows.

Current content mirrors `mlp_smoke_v1` intentionally; replace models here when
broadening the benchmark suite.

Generate or refresh ONNX files:

```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out runs/models/mlp_smoke_v2/mlp1.onnx
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp2 --out runs/models/mlp_smoke_v2/mlp2.onnx
sha256sum runs/models/mlp_smoke_v2/mlp1.onnx runs/models/mlp_smoke_v2/mlp2.onnx
```

If binaries are regenerated, update `manifest.json` hashes.

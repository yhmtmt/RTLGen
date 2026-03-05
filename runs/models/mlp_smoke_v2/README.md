# MLP Smoke Model Set (`mlp_smoke_v2`)

Purpose: next revisioned benchmark-set identity for campaign expansion while
keeping model provenance explicit in result rows.

Current content uses scaled MLP presets to move beyond placeholder smoke size:
- `mlp1.onnx`: `mlp3` preset (`b=32, in=512, hidden=1024, out=512`)
- `mlp2.onnx`: `mlp4` preset (`b=64, in=1024, hidden=2048, out=4096`) to
  exercise mapper split/tiling path on `minimal.yml`.

Generate or refresh ONNX files:

```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp3 --out runs/models/mlp_smoke_v2/mlp1.onnx
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp4 --out runs/models/mlp_smoke_v2/mlp2.onnx
sha256sum runs/models/mlp_smoke_v2/mlp1.onnx runs/models/mlp_smoke_v2/mlp2.onnx
```

If binaries are regenerated, update `manifest.json` hashes.

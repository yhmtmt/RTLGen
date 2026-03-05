# MLP Smoke Model Set (`mlp_smoke_v0`)

This model set is shared by Layer2 bring-up campaigns.

Generate models:

```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out runs/models/mlp_smoke_v0/mlp1.onnx
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp2 --out runs/models/mlp_smoke_v0/mlp2.onnx
sha256sum runs/models/mlp_smoke_v0/mlp1.onnx runs/models/mlp_smoke_v0/mlp2.onnx
```

Update `manifest.json` if ONNX binaries are regenerated.

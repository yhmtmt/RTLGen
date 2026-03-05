# ONNX Practical Model Set (`onnx_practical_v1`)

Purpose: first practical-scale Layer2 benchmark set beyond smoke-only sizes.

Current content uses larger MLP graphs that exercise both non-split and
split-required mapper paths on `minimal.yml`:
- `mlp_p1.onnx`: `(b=32, in=512, hidden=2048, out=1024)`
- `mlp_p2.onnx`: `(b=64, in=1024, hidden=2048, out=4096)` (split-required)
- `mlp_p3.onnx`: `(b=16, in=1024, hidden=2048, out=2048)`

Regenerate files (deterministic zero-initialized weights):

```sh
python3 - <<'PY'
from pathlib import Path
from npu.mapper.onnx_lite import build_mlp_model_bytes, TENSOR_INT8
models = [
    ("mlp_p1.onnx", "mlp_p1", 32, 512, 2048, 1024),
    ("mlp_p2.onnx", "mlp_p2", 64, 1024, 2048, 4096),
    ("mlp_p3.onnx", "mlp_p3", 16, 1024, 2048, 2048),
]
out_dir = Path("runs/models/onnx_practical_v1")
out_dir.mkdir(parents=True, exist_ok=True)
for fn, name, b, i, h, o in models:
    data = build_mlp_model_bytes(
        name=name,
        b=b,
        in_dim=i,
        hidden_dim=h,
        out_dim=o,
        dtype=TENSOR_INT8,
    )
    (out_dir / fn).write_bytes(data)
PY
sha256sum runs/models/onnx_practical_v1/*.onnx
```

If binaries are regenerated, update `manifest.json` hashes.

# onnx_terminal_vecop_suite_v1

Locally generated measurement-first ONNX suite for bounded terminal vec-op
mapper work.

Current first-pass scope:
- standalone terminal `Relu`
- fixed `nm1`
- non-fused references first

Generator:
- `python3 npu/mapper/examples/gen_terminal_vecop_suite_lite.py --out-dir runs/models/onnx_terminal_vecop_suite_v1`

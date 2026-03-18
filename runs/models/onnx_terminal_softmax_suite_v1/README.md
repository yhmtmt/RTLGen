# ONNX Terminal Softmax Suite v1

This directory holds a small locally generated imported-style Softmax-tail
suite used for staged terminal-output evaluation.

Generation command:

```bash
python3 npu/mapper/examples/gen_softmax_classifier_suite_lite.py \
  --out-dir runs/models/onnx_terminal_softmax_suite_v1
```

The suite intentionally stays inside the current mapper-supported ONNX subset:

- optional `Cast`
- `Gemm`
- terminal `Softmax`
- optional side-output `ArgMax/Gather`

It is a bounded terminal-sensitivity probe, not yet a full non-MLP model suite.

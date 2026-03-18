# ONNX Terminal Direct-Output Suite v1

This directory holds a small locally generated terminal-output suite for the
first mapper-generalization pass beyond terminal `Softmax`.

The bounded first-pass family is:
- terminal linear output
- terminal `Relu` output

The suite intentionally stays inside the current sequential-Gemm mapper subset:
- optional `Flatten`
- terminal `Gemm`
- optional terminal `Relu`

Generation command:

```bash
python3 npu/mapper/examples/gen_terminal_direct_output_suite_lite.py \
  --out-dir runs/models/onnx_terminal_direct_output_suite_v1
```

This is a measurement-first legality and reference-point suite, not yet a
broader non-MLP workload claim.

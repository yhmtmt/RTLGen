# Design Brief

## Objective
- add bounded terminal `HardSigmoid` lowering to the mapper direct-output path
- generate a bounded hard-sigmoid-first ONNX suite
- stage the evaluation as:
  - `measurement_only` baseline first
  - dependency-gated `paired_comparison` second

## Scope Guard
- fixed architecture: accepted `fp16_nm1_hardsigmoidproxy`
- no nm1 vs nm2 ranking in this pass
- no broad activation-family claim beyond bounded hard-sigmoid

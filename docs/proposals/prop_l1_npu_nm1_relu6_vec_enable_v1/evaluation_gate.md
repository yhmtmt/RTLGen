# Evaluation Gate

## Required Before Remote Evaluation
- integrated `nm1` ReLU6 vec support implemented locally
- local legality / smoke checks pass
- a bounded reduced physical target is identified before broadening the sweep

## Remote Evaluation Shape
- first remote item:
  - `task_type`: `l1_sweep`
  - `evaluation_mode`: `measurement_only`
  - `objective`: `npu_nm1_relu6_vec_physical_metrics`
  - `abstraction_layer`: `architecture_block`

## Acceptance Rule
- do not queue any Layer 2 terminal `ReLU6` campaign until one
  integrated ReLU6-enabled `nm1` source has merged physical evidence

# Evaluation Gate

## Required Before Remote Evaluation
- integrated `nm1` hard-tanh vec support implemented locally
- local legality / smoke checks pass
- a bounded reduced physical target is identified before broadening the sweep

## Remote Evaluation Shape
- first remote item:
  - `task_type`: `l1_sweep`
  - `evaluation_mode`: `measurement_only`
  - `objective`: `npu_nm1_hardtanh_vec_physical_metrics`
  - `abstraction_layer`: `architecture_block`

## Acceptance Rule
- do not queue any Layer 2 terminal `hard-tanh` campaign until one
  integrated hard-tanh-enabled `nm1` source has merged physical evidence

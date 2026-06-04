# Implementation Summary

## Scope
- Add `8x16`, `16x8`, and `16x16 p2` dense GEMM tile configs.
- Add a hierarchy-preserving Nangate45 scaling sweep.
- Reuse the dense GEMM tile generator and structural guard from V1.

## Validation
- `cmake -S . -B build && cmake --build build --target rtlgen`
- Generated local RTL and passed `check_dense_gemm_tile_guard.py` for
  `8x16`, `16x8`, and `16x16 p2`.
- Targeted dense-tile Layer 1 task-generator test passed.
- `python3 scripts/validate_runs.py --skip_eval_queue`
- `python3 scripts/build_runs_index.py` confirmed `runs/index.csv` unchanged.

## Evaluation Request
- requested task: `l1_npu_dense_gemm_tile_scaling_v2`
- cost class: medium

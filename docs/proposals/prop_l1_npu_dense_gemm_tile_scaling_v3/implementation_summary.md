# Implementation Summary

## Scope

- Add exact-FP16 dense GEMM tile configs:
  - `16x16 k1 p1`
  - `16x16 k2 p2`
  - `16x16 k4 p2` as a prepared boundary point, not part of the first
    dispatch.
- Add a V3 hierarchy-preserving Nangate45 sweep with a larger macro floorplan.
- Reuse the existing dense GEMM tile generator and structural guard.

## Local Validation

- `cmake -S . -B build && cmake --build build --target rtlgen`
- temporary RTL generation and `check_dense_gemm_tile_guard.py` passed for:
  - `16x16 k1 p1` with 256 MAC/cycle
  - `16x16 k2 p2` with 512 MAC/cycle
  - `16x16 k4 p2` with 1024 MAC/cycle

## Evaluation Request

- requested task: `l1_npu_dense_gemm_tile_scaling_v3`
- dispatch machine: `eval-daemon-b7c2d9c80c1c`
- cost class: medium

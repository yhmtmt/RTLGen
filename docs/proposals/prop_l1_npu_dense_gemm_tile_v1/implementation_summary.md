# Implementation Summary

## Scope
- Add `npu/rtlgen/gen_dense_gemm_tile.py`.
- Add `4x4` and `8x8` dense-tile configs under `runs/designs/npu_blocks`.
- Add a hierarchy-preserving Nangate45 sweep under
  `runs/campaigns/npu/dense_gemm_tile_v1`.
- Wire dense-tile configs into the Layer 1 task generator.

## Validation
- `cmake -S . -B build && cmake --build build --target rtlgen`
- `python3 -m py_compile npu/rtlgen/gen_dense_gemm_tile.py npu/eval/check_dense_gemm_tile_guard.py`
- Generated local RTL and passed `check_dense_gemm_tile_guard.py` for both
  `4x4` and `8x8` configs.
- Targeted Layer 1 task-generator tests passed.
- `python3 scripts/validate_runs.py --skip_eval_queue`

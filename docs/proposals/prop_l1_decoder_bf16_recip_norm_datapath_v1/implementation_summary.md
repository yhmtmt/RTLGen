# Implementation Summary

## Scope
- Added RTLGen support for `bf16_recip_norm` in PR #300.
- Added row-8 L1 design collateral and a Nangate45 high-utilization sweep.
- Enabled `SYNTH_MEMORY_MAX_BITS=32768` in PR #303 after r1 showed the
  reciprocal LUT exceeded the default Yosys memory-size gate.

## Evaluation Request
- item: `l1_decoder_bf16_recip_norm_datapath_v1_r2`
- source commit: `604d30b4165ef8b79b16997782979e7313735615`
- result: `status=ok`

## Files Of Interest
- `src/rtlgen/rtl_operations.cpp`
- `examples/config_bf16_recip_norm.json`
- `runs/designs/activations/bf16_recip_norm_r8_wrapper/config_bf16_recip_norm_r8.json`
- `runs/designs/activations/bf16_recip_norm_r8_wrapper/metrics.csv`
- `control_plane/shadow_exports/l1_promotions/l1_decoder_bf16_recip_norm_datapath_v1_r2.json`

## Validation
- `cmake --build /workspaces/RTLGen/build -j2`
- `tests/test_bf16_recip_norm.sh`
- `bash tests/test_softmax_rowwise.sh`
- `PYTHONPATH=/workspaces/RTLGen:/workspaces/RTLGen/control_plane /workspaces/RTLGen/control_plane/.venv/bin/pytest -q control_plane/control_plane/tests/test_l1_task_generator.py`

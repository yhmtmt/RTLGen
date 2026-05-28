# Quality Gate

Required before source-enabling PR merge:

- `cmake --build build --target rtlgen` succeeds
- `tests/test_attention_kv_reducer.sh` passes
- generated Verilog exposes stable reduced values and observable counters
- wrapper generation accepts the reducer config
- dry-run sweep accepts the smoke and frontier config paths
- no evaluator dispatch is attempted before the required config and sweep paths
  exist in a merged commit

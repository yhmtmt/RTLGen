# Quality Gate

Required before source-enabling PR merge:

- `cmake --build build --target rtlgen` succeeds
- `tests/test_attention_kv_reducer_tree.sh` passes
- generated Verilog exposes stable reduced values and observable counters
- wrapper generation accepts the tree reducer config
- dry-run sweep accepts the tree config and sweep paths

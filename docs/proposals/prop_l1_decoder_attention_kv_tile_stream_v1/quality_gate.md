# Quality Gate

Required before source-enabling PR merge:

- `cmake --build /workspaces/RTLGen/build` or equivalent local build succeeds
- generated Verilog exists for the smoke config
- generated Verilog exposes stable cycle and byte counters or equivalent
  observable signals
- local tests cover at least one deterministic vector for the perf model and RTL
  counter contract
- no evaluator dispatch is attempted before the required config and sweep paths
  exist in a merged commit

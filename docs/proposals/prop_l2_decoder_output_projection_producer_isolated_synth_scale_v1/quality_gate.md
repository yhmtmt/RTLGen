# Quality Gate

The run is acceptable if:

- the command manifest uses `--top gemm_compute_array`
- the config list includes nm1, nm2, nm3, and nm4 producer configs
- the report records per-point status and elapsed time
- timeout or stall classifications are preserved as evidence rather than retried indefinitely


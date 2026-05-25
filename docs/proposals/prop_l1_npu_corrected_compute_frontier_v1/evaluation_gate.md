# Evaluation Gate

The guard item must pass before interpreting new PPA rows:

- `tests/test_npu_contract_equivalence.py` passes under plain `python3`
- `npu/eval/check_npu_compute_module_guard.py` reports `status=ok`
- nm1/nm2/nm4 generated RTL localparams and vector register counts match
  `compute.gemm.num_modules`

The stability and boundary sweeps should keep flat/hier results separated and
record `flow_failed` or stalled points instead of repeated long retries.

# Quality Gate

- `pytest -q tests/test_local_reducer_aggregate_aligned_exact_codec.py`
- Require exact 419-bit round-trip under arbitrary input and output stalls.
- Require zero phase-1 padding and sticky malformed-framing detection.
- Require no inter-beat flit bubble under always-ready operation.
- Require generated hierarchy Icarus elaboration and Yosys process/check.

Status: passed locally; physical evaluation pending.

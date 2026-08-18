# Quality Gate

- `pytest -q tests/test_noc_descriptor_command_prefetch.py tests/test_noc_descriptor_pair_scheduler.py`
- Require valid-command RX-before-TX ordering and held-valid backpressure.
- Require invalid commands to set sticky `protocol_error` without submission.
- Require all generated scheduler sources in OpenROAD `VERILOG_FILES`.
- Require one-cycle command-memory response buffering and in-order delivery.
- Require generated wrapper elaboration with Icarus Verilog.

Status: passed locally; physical evaluation pending.

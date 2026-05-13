# Evaluation Gate

Accept the job if it:

- builds or verifies `build/rtlgen` before RTL generation
- generates producer RTL for nm1 and nm2
- runs `npu/synth/run_block_sweep.py` with `--top gemm_compute_array`
- uses the clockless `nangate45_isolated_synth` sweep
- reports whether nm1 and nm2 complete `1_2_yosys` within the timeout
- keeps committed artifact paths repo-portable

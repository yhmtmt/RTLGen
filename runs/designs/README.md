Runs Designs
============

This directory stores per-design artifacts produced by RTL generation and
OpenROAD evaluation.

Layout
------
- `runs/designs/<circuit_type>/<design>/config.json` or equivalent config file
- `runs/designs/<circuit_type>/<design>/verilog/*.v`
- `runs/designs/<circuit_type>/<design>/metrics.csv`
- `runs/designs/<circuit_type>/<design>/work/` (scratch)

Notes on NPU blocks
-------------------
- For block-level NPU macros, use a dedicated circuit_type (e.g., `npu_blocks`).
- Use `npu/synth/run_block_sweep.py` to run OpenROAD sweeps on these blocks.

Notes
-----
- `metrics.csv` is append-only. Each row is one evaluation run.
- Avoid committing large logs or DEF/GDS files; keep only what is needed for
  reproducibility and indexing.
- The global index is generated from these directories by
  `scripts/build_runs_index.py`.

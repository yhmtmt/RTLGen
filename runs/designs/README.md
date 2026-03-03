Runs Designs
============

This directory stores per-design artifacts produced by RTL generation and
OpenROAD evaluation.

Layer interpretation
--------------------
- Layer 1 (circuit module exploration): primary home for generated module RTL
  + physical sweep metrics.
- Layer 2 (NPU architecture exploration): stores NPU block and macro-hardening
  artifacts used by campaign-level model evaluations.

Layout
------
- `runs/designs/<circuit_type>/<design>/config.json` or equivalent config file
- `runs/designs/<circuit_type>/<design>/verilog/*.v`
- `runs/designs/<circuit_type>/<design>/metrics.csv`
- `runs/designs/<circuit_type>/<design>/work/` (scratch)
- `runs/designs/npu_macros/<macro_id>/macro_manifest.json` for hardened
  macro exchange into hierarchical NPU top-level sweeps.

Notes on NPU blocks
-------------------
- For block-level NPU macros, use a dedicated circuit_type (e.g., `npu_blocks`).
- Use `npu/synth/run_block_sweep.py` to run OpenROAD sweeps on these blocks.
- For hardened reusable macros, use `npu/synth/pre_synth_compute.py` and keep
  macro manifests in `runs/designs/npu_macros/`.

Notes
-----
- `metrics.csv` is append-only. Each row is one evaluation run.
- Avoid committing large logs or DEF/GDS files; keep only what is needed for
  reproducibility and indexing.
- The global index is generated from these directories by
  `scripts/build_runs_index.py`.

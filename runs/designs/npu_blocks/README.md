# NPU Blocks (Designs)

This folder holds block-level NPU macros for OpenROAD evaluation.
Each block is a standalone RTL module with its own `verilog/` and `metrics.csv`.

Recommended flow:
- Populate `runs/designs/npu_blocks/<block>/verilog/*.v`
- If the block is tiny, add a minimal `pdn.tcl` and pass it via `PDN_TCL` in the sweep JSON.
- Run `python3 npu/synth/run_block_sweep.py --design_dir runs/designs/npu_blocks/<block> ...`

# Evaluation Gate

Accept the job if it:

- generates producer RTL for each attempted config
- runs `npu/synth/run_block_sweep.py` with `--make_target 1_2_yosys`
- applies both total and quiet-output timeouts per point
- stops after the first nonviable point unless explicitly configured otherwise
- writes JSON and Markdown reports with largest completed and first nonviable `num_modules`
- keeps artifact paths repo-portable

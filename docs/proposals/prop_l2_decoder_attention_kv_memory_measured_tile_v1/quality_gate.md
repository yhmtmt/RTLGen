# Quality Gate

- The estimator must run from committed repository inputs only.
- The committed JSON output must keep full analytical sweep detail compact.
- The measured tile section must identify its source metrics paths.
- The measured tile section must not claim full SRAM, NoC, softmax, or
  producer-coupled calibration.
- `scripts/validate_runs.py --skip_eval_queue` must pass after artifact merge.

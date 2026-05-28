# Quality Gate

Required before result promotion:

- the worker command sequence completes without command failure
- each generated wrapper `metrics.csv` has rows with a `status` column
- non-ok rows are accepted only as boundary evidence
- result artifacts stay lightweight
- `scripts/build_runs_index.py` and `scripts/validate_runs.py --skip_eval_queue`
  pass in the evaluator checkout

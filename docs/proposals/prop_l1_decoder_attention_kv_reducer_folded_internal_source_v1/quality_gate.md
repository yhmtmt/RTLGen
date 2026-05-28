# Quality Gate

- `cmake --build build --target rtlgen` passes.
- `tests/test_attention_kv_reducer_folded.sh` passes.
- `python3 scripts/run_sweep.py ... --dry_run` covers all four internal-source configs.
- `python3 scripts/validate_runs.py --skip_eval_queue` passes.

# DB-Native Real Layer1 Run

Archive note:
- historical execution log
- retained for implementation history, not operator workflow

Date: 2026-03-10

## Scope

Validate the DB-native Layer1 generator -> worker -> result-consumer path against the real RTLGen repo and real OpenROAD-facing commands, without going through queue JSON.

## Setup

- Repo root: `/workspaces/RTLGen`
- DB: `sqlite+pysqlite:////tmp/rtlcp_real_l1_main.db`
- Work item: `l1_real_softmax_shadow_single`
- Run key: `l1_real_softmax_shadow_single_run_ce8a0c531482c099`
- Config: `examples/config_softmax_rowwise_int8.json`
- Sweep: `control_plane/shadow_exports/sweeps/nangate45_softmax_single.json`
- Output root: `control_plane/shadow_exports/l1_runs`

The sweep was intentionally reduced to one OpenROAD point and written under `control_plane/shadow_exports/` so the proof exercised real scripts without dirtying tracked `runs/` outputs.

## Result

The real DB-native Layer1 run succeeded.

- Work item final state: `AWAITING_REVIEW`
- Run status: `SUCCEEDED`
- Worker summary: `4/4 commands succeeded`
- Run window:
  - start: `2026-03-10 05:53:29 UTC`
  - complete: `2026-03-10 06:12:15 UTC`

Observed command chain:

1. `build_generator`
2. `run_sweep`
3. `build_runs_index`
4. `validate`

During `run_sweep`, the worker reached the real ORFS flow stages including Yosys, floorplan, CTS, and detail route before completing.

## Produced Metrics

Generated metrics row:

- wrapper: `softmax_rowwise_int8_r4_wrapper`
- platform: `nangate45`
- `param_hash`: `e9a72134`
- `tag`: `softmax_rowwise_shadow_single_6f920ca2`
- `critical_path_ns`: `12.5074`
- `die_area`: `35611.4641`
- `total_power_mw`: `0.188`
- `result_path`: `/workspaces/RTLGen/control_plane/shadow_exports/l1_runs/softmax_rowwise_int8_r4_wrapper/work/e9a72134/result.json`

Metrics file:

- `control_plane/shadow_exports/l1_runs/softmax_rowwise_int8_r4_wrapper/metrics.csv`

## Consumer Output

The Layer1 result consumer succeeded and wrote:

- `control_plane/shadow_exports/l1_promotions/l1_real_softmax_shadow_single.json`

Proposal summary:

- `proposal_count = 1`
- selected `param_hash = e9a72134`
- selected `result_path = /workspaces/RTLGen/control_plane/shadow_exports/l1_runs/softmax_rowwise_int8_r4_wrapper/work/e9a72134/result.json`

## Issues Found And Fixed

1. `build_generator` assumed an existing `build/` directory.
   - Fix: generate Layer1 work items with `cmake -S . -B build && cmake --build build --target rtlgen`.

2. Layer1 result consumption used plain CSV parsing.
   - Real `metrics.csv` rows still contain historical unquoted JSON in `params_json`.
   - Fix: use the same tolerant parser shape as `scripts/build_runs_index.py` so `result_path` is recovered correctly.

## Conclusion

The DB-native Layer1 path is now validated against the real hydrated repo and real OpenROAD-facing execution, not only against a stub repo.

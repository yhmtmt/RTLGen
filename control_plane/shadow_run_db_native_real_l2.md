# DB-Native Real Layer2 Run

Archive note:
- historical execution log
- retained for implementation history, not operator workflow

Date: 2026-03-10

## Scope

Validate the DB-native Layer2 generator -> worker -> result-consumer path against the real RTLGen repo and real OpenROAD-facing commands, without going through queue JSON.

## Setup

- Repo root: `/workspaces/RTLGen`
- DB: `sqlite+pysqlite:////tmp/rtlcp_real_l2_main.db`
- Work item: `l2_real_softmax_shadow_single`
- Run key: `l2_real_softmax_shadow_single_run_b8dd42dfa6c779a2`
- Campaign: `control_plane/shadow_exports/campaigns/l2_softmax_macro_single.json`
- Output root: `control_plane/shadow_exports/campaigns/l2_softmax_macro_single`

The campaign was intentionally narrowed to one model and one architecture point, with outputs under `control_plane/shadow_exports/`, so the proof exercised the real Layer2 stack without dirtying tracked `runs/` outputs.

## Result

The real DB-native Layer2 run succeeded.

- Work item final state: `AWAITING_REVIEW`
- Run status: `SUCCEEDED`
- Worker summary: `5/5 commands succeeded`
- Run window:
  - start: `2026-03-10 06:18:17 UTC`
  - complete: `2026-03-10 06:56:46 UTC`

Observed command chain:

1. `validate_campaign`
2. `run_campaign`
3. `report_campaign`
4. `objective_sweep`
5. `validate_runs`

During `run_campaign`, the worker entered the real physical path:

- `npu/eval/run_campaign.py`
- `npu/synth/run_block_sweep.py`
- ORFS/Yosys/OpenROAD execution for both `flat_nomacro` and `hier_macro`
- concrete stages observed included Yosys, floorplan, global placement, CTS, and detail route / place-GP mode transitions depending on the mode path

## Produced Outputs

Generated campaign outputs:

- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/results.csv`
- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/summary.csv`
- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/report.md`
- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/best_point.json`
- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/objective_sweep.csv`
- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/objective_sweep.md`
- `control_plane/shadow_exports/campaigns/l2_softmax_macro_single/pareto.csv`

Generated design metrics:

- `control_plane/shadow_exports/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp_shadow_single/metrics.csv`

Summary outcome:

- recommended arch: `fp16_nm1_softmax_r4_shadow_single`
- recommended macro mode: `flat_nomacro`
- aggregate latency: `0.000621 ms`
- aggregate energy: `1.14629148e-07 mJ`
- aggregate critical path: `5.690256573668907 ns`
- aggregate flow elapsed: `1123.33 s`

## Consumer Output

The Layer2 result consumer succeeded and wrote:

- `control_plane/shadow_exports/l2_decisions/l2_real_softmax_shadow_single.json`

Consumer summary:

- `profile_count = 5`
- recommendation:
  - `arch_id = fp16_nm1_softmax_r4_shadow_single`
  - `macro_mode = flat_nomacro`

## Conclusion

The DB-native Layer2 path is now validated against the real hydrated repo and the real OpenROAD-facing campaign stack, not only against the stubbed DB-native demo.

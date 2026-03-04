Evaluation Agent First-Read Guide
=================================

Purpose
-------
This is the first document an evaluator agent should read before running
OpenROAD-heavy tasks.

It defines:
- which documents are authoritative,
- how to execute queued evaluation tasks on high-performance machines,
- how to report results back through GitHub PRs,
- how to keep artifacts reproducible and lightweight.

Scope
-----
- Primary: OpenROAD-based evaluation work for Layer 1 modules and Layer 2 NPU
  blocks.
- Out of scope: algorithm design decisions (handled by development agents).

Read Order (Do This First)
--------------------------
1. `docs/two_layer_workflow.md`
2. `docs/layer1_circuit_workflow.md` (Layer 1 work) and/or
   `npu/docs/workflow.md` (Layer 2 work)
3. `runs/eval_queue/README.md`
4. Queue item assigned to you under:
   - `runs/eval_queue/openroad/queued/*.json`
5. If queue item references candidates:
   - `runs/candidates/<pdk>/module_candidates.json`

Execution Model (Queue -> Evaluated)
------------------------------------
1. Pick a queued item JSON.
2. Create evaluator branch: `eval/<item_id>`.
3. Run commands listed in `task.commands[]` exactly, unless task explicitly
   allows parameter retuning.
4. Commit lightweight outputs only (configs/manifests/RTL/metrics/report rows).
5. Update the item JSON with `result` payload.
6. Move item file from:
   - `runs/eval_queue/openroad/queued/` ->
   - `runs/eval_queue/openroad/evaluated/`
7. Open PR with the requested `handoff.pr_title`.

Queue source-mode contract
--------------------------
Every queue item must declare `task.source_mode`:
- `config`: use `npu/synth/pre_synth_compute.py --config ...` for raw RTLGen
  modules emitted directly by config.
- `src_verilog`: use `npu/synth/pre_synth_compute.py --src_verilog_dir ...`
  for already-generated RTL directories (including `*_wrapper` modules).

Wrapper rule:
- If `--module` ends with `_wrapper`, `source_mode` must be `src_verilog`.
  Do not queue wrapper hardening in `config` mode.

Clocking rule for sequential wrappers:
- If wrapper module has clocked IO registers, include `--clock_port clk` in
  hardening command; leaving clock port empty can yield invalid timing
  (`critical_path_ns=-1.0`).

Mandatory Gates Before PR
-------------------------
Run:
```sh
python3 scripts/validate_runs.py
```

If Layer 2 campaign files are changed, also run:
```sh
python3 npu/eval/validate.py --campaign <campaign.json> --check_paths
```

Do not open PR if validation fails.

Result Payload Rules (evaluated items)
--------------------------------------
For `state=evaluated`, fill `result` with:
- `completed_utc`
- `executor`
- `branch`
- `status` (`ok` / `fail` / `partial`)
- `summary`
- `metrics_rows[]`

`metrics_rows[]` must point to real rows in `metrics.csv` by reference keys:
- required: `metrics_csv`, `platform`, `status`
- plus at least one of: `param_hash` or `tag`
- optional: `result_path`

If `result.status=ok`, include at least one valid metrics row reference.

Artifact Policy
---------------
Allowed in PRs:
- config JSON/YAML, sweep JSON
- generated RTL (`verilog/*.v`, `*.sv`, `*.vh`) when needed
- `metrics.csv`, summary CSV/MD/JSON, candidate/campaign manifests
- queue item move (`queued` -> `evaluated`) and result payload update

Do not commit:
- DEF/GDS/log dumps
- large temporary flow artifacts
- unrelated submodule updates

Evaluation Decision Rules
-------------------------
Classify unexpected outcomes as one of:

1. Flow issue (retune OpenROAD)
- Example symptoms: congestion/PDN failures, unstable timing from density/util.
- Action: sweep flow params (`CORE_UTILIZATION`, `PLACE_DENSITY`,
  `CLOCK_PERIOD`) and keep traceable best row.

2. Design issue (report to development)
- Example symptoms: consistent regression across PDKs/flow settings.
- Action: keep evidence in summary and flag likely root cause.

3. Data issue (repair evaluation records)
- Example symptoms: malformed/missing metrics, outlier with broken row fields.
- Action: rerun or fix metadata paths; keep append-only metrics policy.

Macro-Hardening Specific Rule
-----------------------------
If the goal is hierarchical macro usage, ensure outputs support
`evaluation_scope=macro_hardened` with a valid `macro_manifest`.
Do not leave candidate scope as `wrapped_io` unless explicitly intended.

PR Checklist (copy into description)
------------------------------------
- [ ] Commands from queue item executed (or deviations explained).
- [ ] Queue item moved to `evaluated/` and `result` filled.
- [ ] `metrics_rows` references are valid.
- [ ] `python3 scripts/validate_runs.py` passed.
- [ ] Only lightweight artifacts committed.

Notes
-----
- Keep results append-only and reproducible.
- Prefer explicit traceability (`param_hash`, `tag`, `config_hash`) over
  narrative-only summaries.

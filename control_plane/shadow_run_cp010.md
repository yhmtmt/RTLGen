# CP-010 Shadow Run Note

Purpose:
- document one real control-plane shadow execution against a live repo queue item,
- record exact preconditions, observed behavior, and comparison output,
- keep the proof reviewable without relying on terminal history.

Date:
- 2026-03-08 UTC

Queue item:
- `runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json`

Execution environment:
- temp clone under `/tmp/rtlgen-cp010.JyHQAv/repo`
- temp DB files:
  - `/tmp/rtlgen-cp010.JyHQAv/cp.db`
  - `/tmp/rtlgen-cp010.JyHQAv/cp2.db`

## Commands Used

Import into control-plane DB:
```sh
python3 -m control_plane.cli.main import-queue \
  --database-url sqlite+pysqlite:////tmp/rtlgen-cp010.JyHQAv/cp.db \
  --repo-root /tmp/rtlgen-cp010.JyHQAv/repo \
  --queue-path runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json
```

First worker attempt:
```sh
python3 -m control_plane.cli.main run-worker \
  --database-url sqlite+pysqlite:////tmp/rtlgen-cp010.JyHQAv/cp.db \
  --repo-root /tmp/rtlgen-cp010.JyHQAv/repo \
  --machine-key cp010-worker \
  --hostname cp010-host \
  --capabilities-json '{"platform":"nangate45","flow":"openroad"}' \
  --capability-filter-json '{"platform":"nangate45","flow":"openroad"}' \
  --lease-seconds 1800 \
  --heartbeat-seconds 30 \
  --max-items 1
```

Model fetch precondition:
```sh
python3 npu/eval/fetch_models.py \
  --manifest runs/models/onnx_imported_softmax_tail_v1/manifest.json
```

Second worker attempt:
```sh
python3 -m control_plane.cli.main run-worker \
  --database-url sqlite+pysqlite:////tmp/rtlgen-cp010.JyHQAv/cp2.db \
  --repo-root /tmp/rtlgen-cp010.JyHQAv/repo \
  --machine-key cp010-worker \
  --hostname cp010-host \
  --capabilities-json '{"platform":"nangate45","flow":"openroad"}' \
  --capability-filter-json '{"platform":"nangate45","flow":"openroad"}' \
  --lease-seconds 1800 \
  --heartbeat-seconds 30 \
  --max-items 1
```

Failed-run snapshot sync:
```sh
python3 -m control_plane.cli.main sync-artifacts \
  --database-url sqlite+pysqlite:////tmp/rtlgen-cp010.JyHQAv/cp.db \
  --repo-root /tmp/rtlgen-cp010.JyHQAv/repo \
  --item-id l2_e2e_softmax_macro_tail_v1 \
  --evaluator-id control_plane \
  --session-id s20260308t103000z \
  --host cp010-host \
  --executor @control_plane
```

## Observations

First attempt:
- queue import succeeded
- worker acquired lease and started run
- `validate_campaign` failed immediately because the external ONNX model had not been fetched
- stderr:
  - `campaign.model_manifest.models[0].onnx_path: path does not exist: runs/model_cache/onnx_imported_softmax_tail_v1/logistic_regression.onnx`

Interpretation:
- this is a real evaluator precondition, not a control-plane defect
- the queue item depends on the external model fetch flow documented in:
  - `runs/models/onnx_imported_softmax_tail_v1/README.md`
  - `notes/evaluation_agent_guidance.md`

Second attempt:
- after `fetch_models.py`, `validate_campaign` passed
- worker progressed into:
  - `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/campaign.json --run_physical --jobs 2 --batch_id l2_e2e_softmax_macro_tail_v1_r1`
- `run_campaign.py` launched:
  - `python3 npu/synth/run_block_sweep.py ...`
  - OpenROAD `make ... 3_3_place_gp`
- mapper and perf artifacts were created under:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/artifacts/mapper/...`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/artifacts/perf/...`

Interpretation:
- the control-plane worker executed the real queue item past validation and into the physical synthesis path
- this is sufficient to show that the DB/lease/run/worker integration works on a genuine repo item
- the long-running physical sweep was stopped after evidence capture to avoid leaving background jobs running

## Exported Snapshot Comparison

Exported snapshot path:
- `runs/eval_queue/openroad/evaluated/l2_e2e_softmax_macro_tail_v1.json`

Comparison reference:
- `runs/eval_queue/openroad/evaluated/l2_e2e_onnx_practical_v1_focus_flat_v1.json`

Observed result-shape comparison:
- exported result keys:
  - `branch`
  - `completed_utc`
  - `evaluator_id`
  - `executor`
  - `host`
  - `identity_block`
  - `metrics_rows`
  - `notes`
  - `queue_item_id`
  - `session_id`
  - `status`
  - `summary`
- reference result keys:
  - `branch`
  - `completed_utc`
  - `evaluator_id`
  - `executor`
  - `host`
  - `identity_block`
  - `metrics_rows`
  - `queue_item_id`
  - `session_id`
  - `status`
  - `summary`

Key comparison results:
- branch shape matched:
  - `eval/l2_e2e_softmax_macro_tail_v1/s20260308t103000z`
- identity block shape matched:
  - `[role:evaluator][account:control_plane][session:s20260308t103000z][host:cp010-host][item:l2_e2e_softmax_macro_tail_v1]`
- result status for the first attempt was correctly exported as:
  - `fail`
- `metrics_rows` was an empty array, which is valid for a failed evaluated item

## Follow-up Fixes Applied During CP-010

Two control-plane gaps were found and fixed during this run:

1. failed internal runs were not eligible for `sync-artifacts`
- fixed by allowing work-item state `failed` in artifact sync

2. failed runs with missing `metrics.csv` outputs were treated as sync errors
- fixed by allowing missing metrics files when `queue_result.status == "fail"`

These fixes were committed in the main repo control-plane code path, not only in the temp clone.

## Conclusion

What was proven:
- real repo queue item import into DB
- real lease acquisition
- real worker run creation
- real command execution on the live command manifest
- real evaluator precondition failure surfaced cleanly
- real external-model fetch precondition repaired
- real progression into `run_campaign --run_physical`
- real failed-run export into evaluator-compatible queue snapshot shape

What remained at that point for a full-success shadow run:
- let the second post-fetch physical campaign finish to completion on a machine where the OpenROAD runtime window is acceptable
- then sync the succeeded run and compare its `metrics_rows[]` payload against evaluator-issued `ok` snapshots

## Post-merge Success Rerun

Date:
- 2026-03-08 UTC

Merged baseline:
- local `master` updated to:
  - `2fdb53eae974173e842adddd6f7c0f4ae2ec43a8`
- this includes the merged export-shape fix from PR 14

Goal:
- rerun the CP-010 success path using the merged `master`
- confirm that the exported evaluated snapshot now matches the legacy evaluator result shape
- confirm that exported `metrics_rows[*].result_path` values are repo-portable

### Rerun Structure

Cold fresh-clone rerun:
- temp clone:
  - `/tmp/rtlgen-cp010rerun.fCE1Di/repo`
- temp DB:
  - `/tmp/rtlgen-cp010rerun.fCE1Di/cp.db`
- queue import succeeded
- `fetch_models.py` succeeded
- worker run:
  - `l2_e2e_softmax_macro_tail_v1_run_e28581f050666430`
- `validate_campaign` passed
- worker re-entered the real physical path:
  - `run_campaign.py`
  - `run_block_sweep.py`
  - OpenROAD/Yosys under `/orfs/flow/...`

Interpretation:
- merged `master` still exercises the real physical path correctly
- a truly fresh clone has no prior `work/<hash>/result.json` artifacts, so `--skip_existing` does not short-circuit the full multi-hour physical sweep
- this cold rerun was manually interrupted after proof capture to avoid recomputing the entire sweep a second time

Seeded success-path rerun:
- temp clone:
  - `/tmp/rtlgen-cp010seeded.UU88eh/repo`
- temp DB:
  - `/tmp/rtlgen-cp010seeded.UU88eh/cp.db`
- machine identity:
  - `machine_key=cp010-3a18d8e397af`
  - `hostname=3a18d8e397af`
- session id used for artifact sync:
  - `s20260308t184717z`

Method:
- started from a fresh clone of merged `master`
- fetched the external ONNX model again
- imported the live queue item into a fresh control-plane DB
- copied only the previously completed local campaign/work artifacts from the earlier successful shadow run into the fresh clone:
  - `runs/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp/work/`
  - `runs/designs/npu_blocks/npu_fp16_cpp_nm2_softmaxcmp/work/`
  - the corresponding `metrics.csv` files
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/`
- then executed the standard CP-010 worker pass on top of that fresh clone and fresh DB

Reason for seeding:
- this preserves the control-plane success path on merged code while avoiding a redundant full OpenROAD recomputation
- `run_campaign.py --run_physical` still runs through the queue manifest and success path, but can reuse the already completed local physical artifacts via the existing `--skip_existing` behavior

### Seeded Success Result

Worker run:
- `l2_e2e_softmax_macro_tail_v1_run_6a521acce688cb24`

Run outcome:
- worker summary:
  - `5/5 commands succeeded`
- final DB state:
  - `work_item.state=AWAITING_REVIEW`
  - `run.status=SUCCEEDED`
- final run events:
  - `run_started`
  - `checkout_prepared`
  - `command_finished` x5
  - `run_completed`
  - `artifact_synced`

Per-command results:
- `validate_campaign`
  - exit `0`
  - stdout:
    - `OK: campaign runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_v1/campaign.json`
- `run_campaign`
  - exit `0`
  - stdout shows reuse of mapper/perf artifacts and successful completion:
    - `generated_rows=12`
- `report_campaign`
  - exit `0`
  - wrote:
    - `report.md`
    - `summary.csv`
    - `pareto.csv`
    - `best_point.json`
- `objective_sweep`
  - exit `0`
  - wrote objective-profile reports and:
    - `objective_sweep.csv`
    - `objective_sweep.md`
- `validate_runs`
  - exit `0`
  - stdout:
    - `OK: runs validation passed`

### Exported Snapshot Check

Exported snapshot path:
- `runs/eval_queue/openroad/evaluated/l2_e2e_softmax_macro_tail_v1.json`

Reference snapshot:
- `runs/eval_queue/openroad/evaluated/l2_e2e_onnx_practical_v1_focus_flat_v1.json`

Observed exported result:
- `result.status`
  - `ok`
- `result.branch`
  - `eval/l2_e2e_softmax_macro_tail_v1/s20260308t184717z`
- `result.identity_block`
  - `[role:evaluator][account:control_plane][session:s20260308t184717z][host:3a18d8e397af][item:l2_e2e_softmax_macro_tail_v1]`
- `result.metrics_rows`
  - type: `list`
  - count: `12`

Shape comparison:
- exported result keys:
  - `branch`
  - `completed_utc`
  - `evaluator_id`
  - `executor`
  - `host`
  - `identity_block`
  - `metrics_rows`
  - `queue_item_id`
  - `session_id`
  - `status`
  - `summary`
- reference result keys:
  - `branch`
  - `completed_utc`
  - `evaluator_id`
  - `executor`
  - `host`
  - `identity_block`
  - `metrics_rows`
  - `queue_item_id`
  - `session_id`
  - `status`
  - `summary`
- key match result:
  - exact match

Path portability result:
- exported `metrics_rows[*].result_path` values now point at repo-tracked result JSON files, for example:
  - `runs/designs/npu_blocks/npu_fp16_cpp_nm1_softmaxcmp/work/c20283de/result.json`
  - `runs/designs/npu_blocks/npu_fp16_cpp_nm2_softmaxcmp/work/cebcbcaf/result.json`
- the earlier bad patterns are gone:
  - no extra `result.notes`
  - no evaluator-local `/tmp/...` paths
  - no `/orfs/...` OpenROAD log JSON paths in `result.metrics_rows`

### Planner Conclusion

What is now proven:
- merged `master` still imports the live queue item and reaches the real physical execution path in a fresh shadow run
- the CP-010 success path completes cleanly on merged code
- `sync-artifacts` now exports a legacy-compatible evaluated result shape
- exported `metrics_rows[*].result_path` values are repo-portable and validator-compatible
- the original CP-010 blocker on succeeded-run snapshot shape is closed

Remaining caveat:
- the final success validation used a fresh merged clone plus seeded prior local physical artifacts, not a second full cold recomputation of the entire sweep
- this was intentional to avoid redundant OpenROAD runtime after the cold rerun had already proven re-entry into the true physical path on merged `master`

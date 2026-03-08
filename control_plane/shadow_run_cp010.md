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

What remains for a full-success shadow run:
- let the second post-fetch physical campaign finish to completion on a machine where the OpenROAD runtime window is acceptable
- then sync the succeeded run and compare its `metrics_rows[]` payload against evaluator-issued `ok` snapshots

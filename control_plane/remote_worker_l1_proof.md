# Remote Worker L1 Proof

This proves the control plane works across two distinct PCs:

1. the notebook generates a fresh Layer 1 work item in the shared PostgreSQL DB
2. the evaluator PC runs the worker against that DB
3. the notebook consumes the result and optionally opens the submission PR

Assumptions:
- notebook devcontainer role: `server`
- evaluator devcontainer role: `evaluator`
- evaluator PC can already reach PostgreSQL on the notebook host

Shared variables:
- `ITEM_ID`
- `NOTEBOOK_DB_URL`

Suggested `ITEM_ID`:
```sh
export ITEM_ID="l1_remote_softmax_r4_shift5_$(date -u +%Y%m%d%H%M%S)"
```

Notebook DB URL inside the notebook devcontainer:
```sh
export NOTEBOOK_DB_URL='postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane'
```

Evaluator DB URL example:
```sh
export NOTEBOOK_DB_URL='postgresql+psycopg://rtlgen:rtlgen@<notebook-host-ip>:5432/rtlgen_control_plane'
```

## 1. Notebook Prepare

Run:
```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_l1_proof_notebook_prepare.sh
```

This creates one fresh DB-native Layer 1 sweep item under:
- `control_plane/shadow_exports/designs/remote_l1_proof/`

## 2. Evaluator Worker

Run:
```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_l1_proof_evaluator_run.sh
```

This runs exactly one worker pass and should finish with:
- `work_item_state = AWAITING_REVIEW`
- `run_status = SUCCEEDED`

## 3. Notebook Finalize

Run:
```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" \
  /workspaces/RTLGen/control_plane/scripts/remote_l1_proof_notebook_finalize.sh
```

This:
- consumes the Layer 1 result
- prints submission eligibility
- optionally runs `operate-submission` when `RUN_OPERATE_SUBMISSION=1`

Example:
```sh
ITEM_ID="$ITEM_ID" NOTEBOOK_DB_URL="$NOTEBOOK_DB_URL" RUN_OPERATE_SUBMISSION=1 \
  /workspaces/RTLGen/control_plane/scripts/remote_l1_proof_notebook_finalize.sh
```

Expected success condition:
- evaluator PC owns the run execution
- notebook sees the completed run in the shared DB
- submission status reports the item as eligible
- optional submission creates a draft PR from the notebook side

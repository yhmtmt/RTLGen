#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/RTLGen
source "${ROOT}/control_plane/.venv/bin/activate"

DB_URL=${NOTEBOOK_DB_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}
ITEM_ID=${ITEM_ID:?Set ITEM_ID to the retry probe work item}
export DB_URL ITEM_ID

echo "Verifying remote retry probe item:"
echo "  ITEM_ID=${ITEM_ID}"
echo "  DB_URL=${DB_URL}"

PYTHONPATH="${ROOT}/control_plane" python3 - <<'PY'
import json
import os
from control_plane.db import build_engine, build_session_factory
from control_plane.models.runs import Run
from control_plane.models.work_items import WorkItem

db_url = os.environ["DB_URL"]
item_id = os.environ["ITEM_ID"]

engine = build_engine(db_url)
session_factory = build_session_factory(engine)

with session_factory() as session:
    work_item = session.query(WorkItem).filter_by(item_id=item_id).one()
    runs = session.query(Run).filter_by(work_item_id=work_item.id).order_by(Run.attempt.asc()).all()
    summary = {
        "item_id": item_id,
        "work_item_state": work_item.state.value,
        "run_count": len(runs),
        "runs": [
            {
                "run_key": run.run_key,
                "attempt": run.attempt,
                "status": run.status.value,
                "failure_classification": (run.result_payload or {}).get("failure_classification"),
                "retry_decision": (run.result_payload or {}).get("retry_decision"),
            }
            for run in runs
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
PY

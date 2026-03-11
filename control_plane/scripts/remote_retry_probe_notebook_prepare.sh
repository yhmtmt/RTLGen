#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/RTLGen
source "${ROOT}/control_plane/.venv/bin/activate"

DB_URL=${NOTEBOOK_DB_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}
ITEM_ID=${ITEM_ID:-retry_remote_probe_$(date -u +%Y%m%d%H%M%S)}

echo "Preparing remote retry probe item:"
echo "  ITEM_ID=${ITEM_ID}"
echo "  DB_URL=${DB_URL}"

PYTHONPATH="${ROOT}/control_plane" python3 - <<'PY'
import os
from control_plane.db import build_engine, build_session_factory, create_all
from control_plane.models.enums import FlowName, LayerName, WorkItemState
from control_plane.models.task_requests import TaskRequest
from control_plane.models.work_items import WorkItem

db_url = os.environ["DB_URL"]
item_id = os.environ["ITEM_ID"]

engine = build_engine(db_url)
create_all(engine)
session_factory = build_session_factory(engine)

with session_factory() as session:
    task = TaskRequest(
        request_key=f"retry_probe:{item_id}",
        source="remote_retry_probe",
        requested_by="@yhmtmt",
        title=f"Remote retry probe {item_id}",
        description="Intentional timeout probe for remote worker retry behavior",
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        priority=1,
        request_payload={"item_id": item_id, "probe": "remote_retry"},
    )
    session.add(task)
    session.flush()
    work_item = WorkItem(
        work_item_key=f"retry_probe:{item_id}",
        task_request_id=task.id,
        item_id=item_id,
        layer=LayerName.LAYER1,
        flow=FlowName.OPENROAD,
        platform="nangate45",
        task_type="retry_probe",
        state=WorkItemState.READY,
        priority=1,
        source_mode="config",
        input_manifest={},
        command_manifest=[
            {
                "name": "slow_timeout_probe",
                "run": "python3 -c \"import time; time.sleep(2)\"",
            }
        ],
        expected_outputs=[],
        acceptance_rules=["first timeout should requeue; second should fail terminally"],
    )
    session.add(work_item)
    session.commit()
PY

echo
echo "Share this ITEM_ID with the evaluator PC:"
echo "  ${ITEM_ID}"

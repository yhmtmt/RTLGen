#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/RTLGen
source "${ROOT}/control_plane/.venv/bin/activate"

DB_URL=${NOTEBOOK_DB_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}
ITEM_ID=${ITEM_ID:?Set ITEM_ID to the remote proof work item}
RUN_OPERATE_SUBMISSION=${RUN_OPERATE_SUBMISSION:-0}

echo "Finalizing remote L1 proof item:"
echo "  ITEM_ID=${ITEM_ID}"
echo "  DB_URL=${DB_URL}"

PYTHONPATH="${ROOT}/control_plane" \
python3 -m control_plane.cli.main consume-l1-result \
  --database-url "${DB_URL}" \
  --repo-root "${ROOT}" \
  --item-id "${ITEM_ID}"

PYTHONPATH="${ROOT}/control_plane" \
python3 -m control_plane.cli.main submission-status \
  --database-url "${DB_URL}" \
  --item-id "${ITEM_ID}" \
  --format table

if [[ "${RUN_OPERATE_SUBMISSION}" == "1" ]]; then
  PYTHONPATH="${ROOT}/control_plane" \
  python3 -m control_plane.cli.main operate-submission \
    --database-url "${DB_URL}" \
    --repo-root "${ROOT}" \
    --repo yhmtmt/RTLGen \
    --item-id "${ITEM_ID}"
fi

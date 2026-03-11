#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/RTLGen
source "${ROOT}/control_plane/.venv/bin/activate"

DB_URL=${NOTEBOOK_DB_URL:?Set NOTEBOOK_DB_URL to the shared PostgreSQL URL}
ITEM_ID=${ITEM_ID:?Set ITEM_ID to the notebook-generated retry probe item}
HOSTNAME_ACTUAL=${HOSTNAME_ACTUAL:-$(hostname)}
MACHINE_KEY=${MACHINE_KEY:-cp-remote-${HOSTNAME_ACTUAL}}

echo "Running remote retry probe worker:"
echo "  ITEM_ID=${ITEM_ID}"
echo "  DB_URL=${DB_URL}"
echo "  MACHINE_KEY=${MACHINE_KEY}"
echo "  HOSTNAME=${HOSTNAME_ACTUAL}"

PYTHONPATH="${ROOT}/control_plane" \
python3 -m control_plane.cli.main run-worker \
  --database-url "${DB_URL}" \
  --repo-root "${ROOT}" \
  --machine-key "${MACHINE_KEY}" \
  --hostname "${HOSTNAME_ACTUAL}" \
  --capability-filter-json '{"platform":"nangate45","flow":"openroad"}' \
  --command-timeout-seconds 1 \
  --max-retry-attempts 2 \
  --max-items 1

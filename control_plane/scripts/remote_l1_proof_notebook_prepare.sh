#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspaces/RTLGen
source "${ROOT}/control_plane/.venv/bin/activate"

DB_URL=${NOTEBOOK_DB_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}
ITEM_ID=${ITEM_ID:-l1_remote_softmax_r4_shift5_$(date -u +%Y%m%d%H%M%S)}

echo "Preparing remote L1 proof item:"
echo "  ITEM_ID=${ITEM_ID}"
echo "  DB_URL=${DB_URL}"

PYTHONPATH="${ROOT}/control_plane" \
python3 -m control_plane.cli.main generate-l1-sweep \
  --database-url "${DB_URL}" \
  --repo-root "${ROOT}" \
  --item-id "${ITEM_ID}" \
  --sweep-path runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json \
  --configs examples/config_softmax_rowwise_int8_r4_shift5.json \
  --platform nangate45 \
  --out-root control_plane/shadow_exports/designs/remote_l1_proof \
  --requested-by @yhmtmt

PYTHONPATH="${ROOT}/control_plane" \
python3 -m control_plane.cli.main submission-status \
  --database-url "${DB_URL}" \
  --item-id "${ITEM_ID}" \
  --format table

echo
echo "Share this ITEM_ID with the evaluator PC:"
echo "  ${ITEM_ID}"

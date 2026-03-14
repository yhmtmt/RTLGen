#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${RTLCP_DATABASE_URL:-}" ]]; then
  echo "ERROR: RTLCP_DATABASE_URL is required" >&2
  exit 2
fi

if [[ -d "$REPO_ROOT/control_plane/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/control_plane/.venv/bin/activate"
fi

export PYTHONPATH="$REPO_ROOT/control_plane${PYTHONPATH:+:$PYTHONPATH}"

format="${RTLCP_STATUS_FORMAT:-table}"
display_db_url="$(printf '%s' "$RTLCP_DATABASE_URL" | sed -E 's#(://[^:]+:)[^@]+@#\\1***@#')"

echo "== Control Plane Daily Ops =="
echo "repo_root=$REPO_ROOT"
echo "database_url=$display_db_url"
echo

echo "== Service Status =="
if [[ -x "$REPO_ROOT/.devcontainer/control_plane_service_ctl.sh" ]]; then
  echo "local worker service:"
  "$REPO_ROOT/.devcontainer/control_plane_service_ctl.sh" status worker || true
  echo "local completion service:"
  "$REPO_ROOT/.devcontainer/control_plane_service_ctl.sh" status completions || true
else
  echo "service status helper not found"
fi

echo

echo "== Operator Status =="
"$REPO_ROOT/control_plane/scripts/operator_status.sh" --format "$format"

echo

echo "== Cleanup Dry Run =="
"$REPO_ROOT/control_plane/scripts/cleanup.sh"

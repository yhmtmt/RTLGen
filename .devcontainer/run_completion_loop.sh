#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspaces/RTLGen}"
VENV_PATH="${VENV_PATH:-$REPO_ROOT/control_plane/.venv}"
SLEEP_SECONDS="${RTLCP_COMPLETION_LOOP_SECONDS:-300}"

source "${VENV_PATH}/bin/activate"

while true; do
  if ! env PYTHONPATH="${REPO_ROOT}/control_plane" \
    /workspaces/RTLGen/control_plane/scripts/process_completions_service.sh
  then
    printf '[%s] completion loop iteration failed\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >&2
  fi
  sleep "${SLEEP_SECONDS}"
done

#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-$REPO_ROOT/control_plane/.venv}"
SLEEP_SECONDS="${RTLCP_COMPLETION_LOOP_SECONDS:-300}"

source "${VENV_PATH}/bin/activate"

while true; do
  if ! env PYTHONPATH="${REPO_ROOT}/control_plane" \
    "${REPO_ROOT}/control_plane/scripts/process_completions_service.sh"
  then
    printf '[%s] completion loop iteration failed\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >&2
  fi
  sleep "${SLEEP_SECONDS}"
done

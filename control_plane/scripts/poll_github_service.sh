#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
DEFAULT_VENV_PATH="/workspaces/RTLGen/control_plane/.venv"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${DEFAULT_VENV_PATH}}"

: "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required}"

source "${VENV_PATH}/bin/activate"

cmd=(
  python3 -m control_plane.cli.main poll-github
  --database-url "${RTLCP_DATABASE_URL}"
  --repo-root "${REPO_ROOT}"
)

if [[ -n "${RTLCP_REPO_SLUG:-}" ]]; then
  cmd+=(--repo "${RTLCP_REPO_SLUG}")
fi

exec env PYTHONPATH="${REPO_ROOT}/control_plane" "${cmd[@]}"

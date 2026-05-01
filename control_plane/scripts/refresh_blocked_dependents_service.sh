#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${REPO_ROOT}/control_plane/.venv}"

: "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required}"

source "${VENV_PATH}/bin/activate"

exec env PYTHONPATH="${REPO_ROOT}/control_plane" \
  python3 -m control_plane.cli.main refresh-blocked-dependents \
  --database-url "${RTLCP_DATABASE_URL}" \
  --repo-root "${REPO_ROOT}"

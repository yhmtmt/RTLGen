#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${REPO_ROOT}/control_plane/.venv}"

HOST="${RTLCP_HOST:-0.0.0.0}"
PORT="${RTLCP_PORT:-8080}"

source "${VENV_PATH}/bin/activate"
exec env PYTHONPATH="${REPO_ROOT}/control_plane" python3 -m control_plane.cli.main serve-api --host "${HOST}" --port "${PORT}"

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspaces/RTLGen}"
DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
SERVICE_REPO_ROOT="${RTLGEN_SERVICE_REPO:-${DEFAULT_SERVICE_REPO}}"
SERVICE_CTL="${SERVICE_REPO_ROOT}/.devcontainer/control_plane_service_ctl.sh"
RUNTIME_DIR="${RTLCP_RUNTIME_DIR:-/tmp/rtlgen-control-plane}"

cd "${SERVICE_REPO_ROOT}"

git pull --ff-only origin master

"${SERVICE_CTL}" stop completions || true
rm -f "${RUNTIME_DIR}/completions.pid"
"${SERVICE_CTL}" start completions
"${SERVICE_CTL}" status completions
tail -n 40 "${RUNTIME_DIR}/completions.log"

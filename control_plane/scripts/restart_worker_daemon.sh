#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspaces/RTLGen}"
SERVICE_CTL="${REPO_ROOT}/.devcontainer/control_plane_service_ctl.sh"
RUNTIME_DIR="${RTLCP_RUNTIME_DIR:-/tmp/rtlgen-control-plane}"

cd "${REPO_ROOT}"

git pull --ff-only origin master

"${SERVICE_CTL}" stop worker || true
rm -f "${RUNTIME_DIR}/worker.pid"
"${SERVICE_CTL}" start worker
"${SERVICE_CTL}" status worker
tail -n 40 "${RUNTIME_DIR}/worker.log"

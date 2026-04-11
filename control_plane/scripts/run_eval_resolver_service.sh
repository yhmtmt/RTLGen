#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
DEFAULT_VENV_PATH="/workspaces/RTLGen/control_plane/.venv"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${DEFAULT_VENV_PATH}}"
POLL_SECONDS="${RTLCP_RESOLVER_POLL_SECONDS:-60}"

: "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required}"

HOSTNAME_ACTUAL="${RTLCP_HOSTNAME:-$(hostname)}"
MACHINE_KEY="${RTLCP_MACHINE_KEY:-eval-daemon-${HOSTNAME_ACTUAL}}"
repo_slug="${RTLCP_RESOLVER_REPO:-${RTLCP_REPO_SLUG:-}}"
if [[ -z "${repo_slug}" ]]; then
  origin_url="$(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || true)"
  if [[ "${origin_url}" =~ github\.com[:/]([^/]+/[^/.]+)(\.git)?$ ]]; then
    repo_slug="${BASH_REMATCH[1]}"
  fi
fi

if [[ -z "${repo_slug}" ]]; then
  echo "RTLCP_RESOLVER_REPO or RTLCP_REPO_SLUG is required for the eval resolver" >&2
  exit 1
fi

source "${VENV_PATH}/bin/activate"

cmd=(
  python3 -m control_plane.cli.main run-eval-resolver
  --database-url "${RTLCP_DATABASE_URL}"
  --repo "${repo_slug}"
  --machine-key "${MACHINE_KEY}"
  --poll-seconds "${POLL_SECONDS}"
)

if [[ -n "${RTLCP_RESOLVER_MAX_POLLS:-}" ]]; then
  cmd+=(--max-polls "${RTLCP_RESOLVER_MAX_POLLS}")
fi

exec env PYTHONPATH="${REPO_ROOT}/control_plane" "${cmd[@]}"

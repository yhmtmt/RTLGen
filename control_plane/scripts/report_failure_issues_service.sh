#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
DEFAULT_VENV_PATH="/workspaces/RTLGen/control_plane/.venv"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${DEFAULT_VENV_PATH}}"

: "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required}"

source "${VENV_PATH}/bin/activate"

repo_slug="${RTLCP_REPO_SLUG:-}"
if [[ -z "${repo_slug}" ]]; then
  origin_url="$(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || true)"
  if [[ "${origin_url}" =~ github\.com[:/]([^/]+/[^/.]+)(\.git)?$ ]]; then
    repo_slug="${BASH_REMATCH[1]}"
  fi
fi

if [[ -z "${repo_slug}" ]]; then
  printf 'RTLCP_REPO_SLUG is required for failed-job issue reporting\n' >&2
  exit 2
fi

cmd=(
  python3 -m control_plane.cli.main report-failure-issues
  --database-url "${RTLCP_DATABASE_URL}"
  --repo "${repo_slug}"
)

if [[ -n "${RTLCP_FAILURE_ISSUE_MAX_ITEMS:-}" ]]; then
  cmd+=(--max-items "${RTLCP_FAILURE_ISSUE_MAX_ITEMS}")
fi

exec env PYTHONPATH="${REPO_ROOT}/control_plane" "${cmd[@]}"

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspaces/RTLGen}"
VENV_PATH="${VENV_PATH:-$REPO_ROOT/control_plane/.venv}"

: "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required}"

source "${VENV_PATH}/bin/activate"

cmd=(
  python3 -m control_plane.cli.main process-completions
  --database-url "${RTLCP_DATABASE_URL}"
  --repo-root "${REPO_ROOT}"
  --evaluator-id "${RTLCP_EVALUATOR_ID:-control_plane}"
  --executor "${RTLCP_EXECUTOR:-@control_plane}"
  --pr-base "${RTLCP_PR_BASE:-master}"
)

if [[ -n "${RTLCP_REPO_SLUG:-}" ]]; then
  cmd+=(--repo "${RTLCP_REPO_SLUG}")
fi

if [[ -n "${RTLCP_ITEM_ID:-}" ]]; then
  cmd+=(--item-id "${RTLCP_ITEM_ID}")
fi

if [[ -n "${RTLCP_SESSION_ID:-}" ]]; then
  cmd+=(--session-id "${RTLCP_SESSION_ID}")
fi

if [[ -n "${RTLCP_BRANCH_NAME:-}" ]]; then
  cmd+=(--branch-name "${RTLCP_BRANCH_NAME}")
fi

if [[ -n "${RTLCP_SNAPSHOT_TARGET_PATH:-}" ]]; then
  cmd+=(--snapshot-target-path "${RTLCP_SNAPSHOT_TARGET_PATH}")
fi

if [[ -n "${RTLCP_PACKAGE_TARGET_PATH:-}" ]]; then
  cmd+=(--package-target-path "${RTLCP_PACKAGE_TARGET_PATH}")
fi

if [[ -n "${RTLCP_WORKTREE_ROOT:-}" ]]; then
  cmd+=(--worktree-root "${RTLCP_WORKTREE_ROOT}")
fi

if [[ -n "${RTLCP_COMMIT_MESSAGE:-}" ]]; then
  cmd+=(--commit-message "${RTLCP_COMMIT_MESSAGE}")
fi

if [[ "${RTLCP_SUBMIT:-0}" == "1" ]]; then
  cmd+=(--submit)
fi

if [[ "${RTLCP_FORCE:-0}" == "1" ]]; then
  cmd+=(--force)
fi

exec env PYTHONPATH="${REPO_ROOT}/control_plane" "${cmd[@]}"

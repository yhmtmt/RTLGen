#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/workspaces/RTLGen}"
DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
SERVICE_REPO_ROOT="${RTLGEN_SERVICE_REPO:-${DEFAULT_SERVICE_REPO}}"
TARGET_REV="${RTLGEN_SERVICE_REPO_TARGET:-origin/master}"

if [[ "${SERVICE_REPO_ROOT}" == "${REPO_ROOT}" ]]; then
  exit 0
fi

if git -C "${SERVICE_REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

mkdir -p "$(dirname "${SERVICE_REPO_ROOT}")"

if [[ -e "${SERVICE_REPO_ROOT}" ]]; then
  if [[ -d "${SERVICE_REPO_ROOT}" ]] && [[ -z "$(ls -A "${SERVICE_REPO_ROOT}" 2>/dev/null)" ]]; then
    rmdir "${SERVICE_REPO_ROOT}"
  else
    echo "service repo path exists but is not a git worktree: ${SERVICE_REPO_ROOT}" >&2
    exit 1
  fi
fi

git -C "${REPO_ROOT}" fetch origin
git -C "${REPO_ROOT}" worktree add "${SERVICE_REPO_ROOT}" "${TARGET_REV}"

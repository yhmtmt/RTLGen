#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
DEFAULT_VENV_PATH="/workspaces/RTLGen/control_plane/.venv"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${DEFAULT_VENV_PATH}}"

: "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required}"

HOSTNAME_ACTUAL="${RTLCP_HOSTNAME:-$(hostname)}"
MACHINE_KEY="${RTLCP_MACHINE_KEY:-eval-daemon-${HOSTNAME_ACTUAL}}"
if [[ -n "${RTLCP_CAPABILITY_FILTER_JSON:-}" ]]; then
  CAPABILITY_FILTER_JSON="${RTLCP_CAPABILITY_FILTER_JSON}"
else
  CAPABILITY_FILTER_JSON='{"platform":"nangate45","flow":"openroad"}'
fi

POLL_SECONDS="${RTLCP_POLL_SECONDS:-15}"
MAX_ITEMS_PER_POLL="${RTLCP_MAX_ITEMS_PER_POLL:-1}"
if [[ -n "${RTLCP_WORKER_CONCURRENCY:-}" ]]; then
  WORKER_CONCURRENCY="${RTLCP_WORKER_CONCURRENCY}"
elif command -v nproc >/dev/null 2>&1; then
  WORKER_CONCURRENCY="$(nproc)"
elif command -v getconf >/dev/null 2>&1; then
  WORKER_CONCURRENCY="$(getconf _NPROCESSORS_ONLN)"
else
  WORKER_CONCURRENCY=1
fi
LEASE_SECONDS="${RTLCP_LEASE_SECONDS:-1800}"
HEARTBEAT_SECONDS="${RTLCP_HEARTBEAT_SECONDS:-30}"
MAX_RETRY_ATTEMPTS="${RTLCP_MAX_RETRY_ATTEMPTS:-2}"
EXECUTOR_KIND="${RTLCP_EXECUTOR_KIND:-local_process}"
AUTO_PROCESS_COMPLETIONS="${RTLCP_AUTO_PROCESS_COMPLETIONS:-1}"
COMPLETION_SUBMIT="${RTLCP_COMPLETION_SUBMIT:-1}"

repo_slug="${RTLCP_COMPLETION_REPO:-${RTLCP_REPO_SLUG:-}}"
if [[ -z "${repo_slug}" ]]; then
  origin_url="$(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || true)"
  if [[ "${origin_url}" =~ github\.com[:/]([^/]+/[^/.]+)(\.git)?$ ]]; then
    repo_slug="${BASH_REMATCH[1]}"
  fi
fi

if [[ "${MAX_ITEMS_PER_POLL}" -lt "${WORKER_CONCURRENCY}" ]]; then
  MAX_ITEMS_PER_POLL="${WORKER_CONCURRENCY}"
fi

source "${VENV_PATH}/bin/activate"

cmd=(
  python3 -m control_plane.cli.main run-worker-daemon
  --database-url "${RTLCP_DATABASE_URL}"
  --repo-root "${REPO_ROOT}"
  --machine-key "${MACHINE_KEY}"
  --hostname "${HOSTNAME_ACTUAL}"
  --executor-kind "${EXECUTOR_KIND}"
  --capability-filter-json "${CAPABILITY_FILTER_JSON}"
  --lease-seconds "${LEASE_SECONDS}"
  --heartbeat-seconds "${HEARTBEAT_SECONDS}"
  --max-retry-attempts "${MAX_RETRY_ATTEMPTS}"
  --poll-seconds "${POLL_SECONDS}"
  --max-items-per-poll "${MAX_ITEMS_PER_POLL}"
  --concurrency "${WORKER_CONCURRENCY}"
)

if [[ -n "${RTLCP_CAPABILITIES_JSON:-}" ]]; then
  cmd+=(--capabilities-json "${RTLCP_CAPABILITIES_JSON}")
fi

if [[ -n "${RTLCP_COMMAND_TIMEOUT_SECONDS:-}" ]]; then
  cmd+=(--command-timeout-seconds "${RTLCP_COMMAND_TIMEOUT_SECONDS}")
fi

if [[ -n "${RTLCP_COMMAND_STALL_TIMEOUT_SECONDS:-}" ]]; then
  cmd+=(--command-stall-timeout-seconds "${RTLCP_COMMAND_STALL_TIMEOUT_SECONDS}")
fi

if [[ -n "${RTLCP_COMMAND_PROGRESS_SECONDS:-}" ]]; then
  cmd+=(--command-progress-seconds "${RTLCP_COMMAND_PROGRESS_SECONDS}")
fi

if [[ -n "${RTLCP_LOG_ROOT:-}" ]]; then
  cmd+=(--log-root "${RTLCP_LOG_ROOT}")
fi

if [[ "${AUTO_PROCESS_COMPLETIONS}" == "1" ]]; then
  cmd+=(--auto-process-completions)
  if [[ -n "${repo_slug}" ]]; then
    cmd+=(--completion-repo "${repo_slug}")
  fi
  cmd+=(--completion-evaluator-id "${RTLCP_EVALUATOR_ID:-control_plane}")
  cmd+=(--completion-executor "${RTLCP_EXECUTOR:-@control_plane}")
  cmd+=(--completion-pr-base "${RTLCP_PR_BASE:-master}")
  if [[ "${COMPLETION_SUBMIT}" == "1" && -n "${repo_slug}" ]]; then
    cmd+=(--completion-submit)
  fi
  if [[ -n "${RTLCP_SESSION_ID:-}" ]]; then
    cmd+=(--completion-session-id "${RTLCP_SESSION_ID}")
  fi
  if [[ -n "${RTLCP_COMPLETION_HOST:-}" ]]; then
    cmd+=(--completion-host "${RTLCP_COMPLETION_HOST}")
  fi
  if [[ -n "${RTLCP_BRANCH_NAME:-}" ]]; then
    cmd+=(--completion-branch-name "${RTLCP_BRANCH_NAME}")
  fi
  if [[ -n "${RTLCP_SNAPSHOT_TARGET_PATH:-}" ]]; then
    cmd+=(--completion-snapshot-target-path "${RTLCP_SNAPSHOT_TARGET_PATH}")
  fi
  if [[ -n "${RTLCP_PACKAGE_TARGET_PATH:-}" ]]; then
    cmd+=(--completion-package-target-path "${RTLCP_PACKAGE_TARGET_PATH}")
  fi
  if [[ -n "${RTLCP_WORKTREE_ROOT:-}" ]]; then
    cmd+=(--completion-worktree-root "${RTLCP_WORKTREE_ROOT}")
  fi
  if [[ -n "${RTLCP_COMMIT_MESSAGE:-}" ]]; then
    cmd+=(--completion-commit-message "${RTLCP_COMMIT_MESSAGE}")
  fi
  if [[ "${RTLCP_FORCE:-0}" == "1" ]]; then
    cmd+=(--completion-force)
  fi
fi

if [[ -n "${RTLCP_MAX_POLLS:-}" ]]; then
  cmd+=(--max-polls "${RTLCP_MAX_POLLS}")
fi

if [[ "${RTLCP_STOP_ON_NO_WORK:-0}" == "1" ]]; then
  cmd+=(--stop-on-no-work)
fi

if [[ "${RTLCP_ALLOW_STALE_CHECKOUT:-0}" == "1" ]]; then
  cmd+=(--allow-stale-checkout)
fi

if [[ "${RTLCP_DISABLE_SCHEDULER_MAINTENANCE:-0}" == "1" ]]; then
  cmd+=(--no-scheduler-maintenance)
fi

exec env PYTHONPATH="${REPO_ROOT}/control_plane" "${cmd[@]}"

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
LEASE_SECONDS="${RTLCP_LEASE_SECONDS:-1800}"
HEARTBEAT_SECONDS="${RTLCP_HEARTBEAT_SECONDS:-30}"
MAX_RETRY_ATTEMPTS="${RTLCP_MAX_RETRY_ATTEMPTS:-2}"
EXECUTOR_KIND="${RTLCP_EXECUTOR_KIND:-local_process}"

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

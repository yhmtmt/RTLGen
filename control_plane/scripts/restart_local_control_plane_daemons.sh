#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
DEFAULT_VENV_PATH="/workspaces/RTLGen/control_plane/.venv"
DEFAULT_DATABASE_URL="postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane"
DEFAULT_REPO_SLUG="yhmtmt/RTLGen"

ACTION="${1:-restart}"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${DEFAULT_VENV_PATH}}"
RUNTIME_DIR="${RTLCP_RUNTIME_DIR:-${REPO_ROOT}/control_plane/runtime_logs/daemons}"
WORKER_LOG_ROOT="${RTLCP_LOG_ROOT:-${REPO_ROOT}/control_plane/runtime_logs/worker_jobs}"

export RTLCP_DATABASE_URL="${RTLCP_DATABASE_URL:-${DEFAULT_DATABASE_URL}}"
export RTLCP_REPO_SLUG="${RTLCP_REPO_SLUG:-${DEFAULT_REPO_SLUG}}"
export RTLCP_RESOLVER_REPO="${RTLCP_RESOLVER_REPO:-${RTLCP_REPO_SLUG}}"
export RTLCP_HOSTNAME="${RTLCP_HOSTNAME:-$(hostname)}"
export RTLCP_MACHINE_KEY="${RTLCP_MACHINE_KEY:-eval-daemon-${RTLCP_HOSTNAME}}"
export RTLCP_CAPABILITY_FILTER_JSON="${RTLCP_CAPABILITY_FILTER_JSON:-{\"platform\":\"nangate45\",\"flow\":\"openroad\"}}"
export RTLCP_WORKER_CONCURRENCY="${RTLCP_WORKER_CONCURRENCY:-16}"
export RTLCP_MAX_ITEMS_PER_POLL="${RTLCP_MAX_ITEMS_PER_POLL:-${RTLCP_WORKER_CONCURRENCY}}"
export RTLCP_AUTO_PROCESS_COMPLETIONS="${RTLCP_AUTO_PROCESS_COMPLETIONS:-1}"
export RTLCP_COMPLETION_SUBMIT="${RTLCP_COMPLETION_SUBMIT:-1}"
export RTLCP_COMPLETION_REPO="${RTLCP_COMPLETION_REPO:-${RTLCP_REPO_SLUG}}"
export RTLCP_LOG_ROOT="${WORKER_LOG_ROOT}"
export RTLGEN_SERVICE_REPO="${REPO_ROOT}"

mkdir -p "${RUNTIME_DIR}" "${WORKER_LOG_ROOT}"

_timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

_python() {
  printf '%s/bin/python' "${VENV_PATH}"
}

_check_import_path() {
  env PYTHONPATH="${REPO_ROOT}/control_plane" "$(_python)" - "${REPO_ROOT}" <<'PY'
import inspect
import sys
from pathlib import Path

import control_plane
import control_plane.services.l2_result_consumer as l2_result_consumer

repo_root = Path(sys.argv[1]).resolve()
expected = repo_root / "control_plane"
paths = [
    Path(inspect.getfile(control_plane)).resolve(),
    Path(inspect.getfile(l2_result_consumer)).resolve(),
]
for path in paths:
    if expected not in path.parents:
        raise SystemExit(f"control_plane import resolved outside service repo: {path} (expected under {expected})")
print(f"control_plane import path OK: {paths[0]}")
PY
}

_pid_file() {
  printf '%s/%s.pid' "${RUNTIME_DIR}" "$1"
}

_log_file() {
  printf '%s/%s.log' "${RUNTIME_DIR}" "$1"
}

_is_running() {
  local pid_file
  pid_file="$(_pid_file "$1")"
  [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" 2>/dev/null
}

_stop_service() {
  local name pid_file
  name="$1"
  pid_file="$(_pid_file "${name}")"
  if _is_running "${name}"; then
    kill "$(cat "${pid_file}")"
    echo "stopped ${name}: pid=$(cat "${pid_file}")"
  else
    echo "${name} not running"
  fi
  rm -f "${pid_file}"
}

_stop_legacy_processes() {
  if [[ "${RTLCP_STOP_LEGACY_PROCESSES:-1}" != "1" ]]; then
    return
  fi
  pkill -f "control_plane.cli.main serve-api" 2>/dev/null || true
  pkill -f "control_plane.cli.main run-dev-resolver" 2>/dev/null || true
  pkill -f "control_plane.cli.main run-worker-daemon" 2>/dev/null || true
  pkill -f "control_plane.cli.main run-eval-resolver" 2>/dev/null || true
}

_start_service() {
  local name log_file pid_file script
  name="$1"
  script="$2"
  log_file="$(_log_file "${name}")"
  pid_file="$(_pid_file "${name}")"
  if _is_running "${name}"; then
    echo "${name} already running: pid=$(cat "${pid_file}") log=${log_file}"
    return
  fi
  : >"${log_file}"
  {
    printf '[%s] service=%s action=start repo_root=%s venv=%s\n' "$(_timestamp)" "${name}" "${REPO_ROOT}" "${VENV_PATH}"
    printf '[%s] service=%s pythonpath=%s\n' "$(_timestamp)" "${name}" "${REPO_ROOT}/control_plane"
  } >>"${log_file}"
  setsid env \
    RTLGEN_SERVICE_REPO="${REPO_ROOT}" \
    REPO_ROOT="${REPO_ROOT}" \
    VENV_PATH="${VENV_PATH}" \
    PYTHONPATH="${REPO_ROOT}/control_plane" \
    "${script}" </dev/null >>"${log_file}" 2>&1 &
  echo "$!" >"${pid_file}"
  sleep 0.5
  if ! _is_running "${name}"; then
    rm -f "${pid_file}"
    echo "failed to start ${name}; see ${log_file}" >&2
    return 1
  fi
  echo "started ${name}: pid=$(cat "${pid_file}") log=${log_file}"
}

_start_all() {
  _check_import_path
  _start_service api "${REPO_ROOT}/control_plane/scripts/run_api_service.sh"
  _start_service dev-resolver "${REPO_ROOT}/control_plane/scripts/run_dev_resolver_service.sh"
  _start_service worker "${REPO_ROOT}/control_plane/scripts/run_worker_daemon_service.sh"
  _start_service eval-resolver "${REPO_ROOT}/control_plane/scripts/run_eval_resolver_service.sh"
}

_stop_all() {
  _stop_service eval-resolver
  _stop_service worker
  _stop_service dev-resolver
  _stop_service api
  _stop_legacy_processes
}

_status_all() {
  local name pid_file log_file
  for name in api dev-resolver worker eval-resolver; do
    pid_file="$(_pid_file "${name}")"
    log_file="$(_log_file "${name}")"
    if _is_running "${name}"; then
      echo "${name} running: pid=$(cat "${pid_file}") log=${log_file}"
    else
      echo "${name} not running"
    fi
  done
}

case "${ACTION}" in
  start)
    _start_all
    ;;
  stop)
    _stop_all
    ;;
  restart)
    _stop_all
    _start_all
    ;;
  status)
    _status_all
    ;;
  check-import)
    _check_import_path
    ;;
  *)
    echo "Usage: $0 <start|stop|restart|status|check-import>" >&2
    exit 1
    ;;
esac

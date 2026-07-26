#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
DEFAULT_REPO_SLUG="yhmtmt/RTLGen"

ACTION="${1:-restart}"
REPO_ROOT="${RTLGEN_SERVICE_REPO:-${REPO_ROOT:-${DEFAULT_SERVICE_REPO}}}"
VENV_PATH="${VENV_PATH:-${REPO_ROOT}/control_plane/.venv}"
RUNTIME_DIR="${RTLCP_RUNTIME_DIR:-${REPO_ROOT}/control_plane/runtime_logs/daemons}"
WORKER_LOG_ROOT="${RTLCP_LOG_ROOT:-${REPO_ROOT}/control_plane/runtime_logs/worker_jobs}"

export RTLCP_REPO_SLUG="${RTLCP_REPO_SLUG:-${DEFAULT_REPO_SLUG}}"
export RTLCP_RESOLVER_REPO="${RTLCP_RESOLVER_REPO:-${RTLCP_REPO_SLUG}}"
export RTLCP_HOSTNAME="${RTLCP_HOSTNAME:-$(hostname)}"
export RTLCP_CAPABILITY_FILTER_JSON="${RTLCP_CAPABILITY_FILTER_JSON:-{\"platform\":\"nangate45\",\"flow\":\"openroad\"}}"
export RTLCP_WORKER_CONCURRENCY="${RTLCP_WORKER_CONCURRENCY:-16}"
export RTLCP_MAX_ITEMS_PER_POLL="${RTLCP_MAX_ITEMS_PER_POLL:-${RTLCP_WORKER_CONCURRENCY}}"
export RTLCP_AUTO_PROCESS_COMPLETIONS="${RTLCP_AUTO_PROCESS_COMPLETIONS:-1}"
export RTLCP_COMPLETION_SUBMIT="${RTLCP_COMPLETION_SUBMIT:-1}"
export RTLCP_COMPLETION_REPO="${RTLCP_COMPLETION_REPO:-${RTLCP_REPO_SLUG}}"
export RTLCP_LOG_ROOT="${WORKER_LOG_ROOT}"
export RTLGEN_SERVICE_REPO="${REPO_ROOT}"

_timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

_usage() {
  echo "Usage: $0 <start|stop|restart|status|check-import|preflight>" >&2
}

_die() {
  echo "$*" >&2
  exit 1
}

_python() {
  printf '%s/bin/python' "${VENV_PATH}"
}

_require_database_url() {
  if [[ -z "${RTLCP_DATABASE_URL:-}" ]]; then
    _die "RTLCP_DATABASE_URL must be exported explicitly for ${ACTION}; managed daemons will not default to localhost."
  fi
}

_require_machine_key() {
  if [[ -z "${RTLCP_MACHINE_KEY:-}" ]]; then
    _die "RTLCP_MACHINE_KEY must be exported explicitly for ${ACTION}; managed evaluator daemons must keep a stable worker identity."
  fi
}

_require_venv() {
  local python_path activate_path
  python_path="$(_python)"
  activate_path="${VENV_PATH}/bin/activate"
  if [[ ! -x "${python_path}" || ! -f "${activate_path}" ]]; then
    _die "Managed daemon preflight requires ${VENV_PATH}/bin/python and ${VENV_PATH}/bin/activate. Set VENV_PATH explicitly when the clean service checkout does not contain its own virtualenv."
  fi
}

_database_host() {
  local url remainder hostport host
  url="${RTLCP_DATABASE_URL:-}"
  if [[ -z "${url}" || "${url}" != *"://"* ]]; then
    echo "n/a"
    return
  fi
  remainder="${url#*://}"
  remainder="${remainder##*@}"
  hostport="${remainder%%/*}"
  hostport="${hostport%%\?*}"
  hostport="${hostport%%#*}"
  if [[ -z "${hostport}" ]]; then
    echo "n/a"
    return
  fi
  if [[ "${hostport}" == \[* ]]; then
    host="${hostport#\[}"
    host="${host%%]*}"
  else
    host="${hostport%%:*}"
  fi
  if [[ -z "${host}" ]]; then
    echo "n/a"
    return
  fi
  echo "${host}"
}

_is_localhost_host() {
  local host
  host="${1,,}"
  [[ "${host}" == "localhost" || "${host}" == "127.0.0.1" || "${host}" == "::1" ]]
}

_validate_database_host() {
  local db_host
  db_host="$(_database_host)"
  if [[ "${RTLCP_DB_MODE:-}" == "remote" || "${RTLCP_ROLE:-}" == "evaluator" ]]; then
    if _is_localhost_host "${db_host}"; then
      _die "RTLCP_DATABASE_URL must not target localhost/127.0.0.1/::1 when RTLCP_DB_MODE=remote or RTLCP_ROLE=evaluator."
    fi
  fi
}

_is_integer() {
  [[ "$1" =~ ^-?[0-9]+$ ]]
}

_validate_persistence_settings() {
  local stop_on_no_work max_polls allow_finite
  stop_on_no_work="${RTLCP_STOP_ON_NO_WORK:-0}"
  max_polls="${RTLCP_MAX_POLLS:-}"
  allow_finite="${RTLCP_ALLOW_FINITE_WORKER_DAEMON:-0}"

  if [[ "${stop_on_no_work}" == "1" && "${allow_finite}" != "1" ]]; then
    _die "RTLCP_STOP_ON_NO_WORK=1 is not allowed for a managed daemon. Leave it persistent or set RTLCP_ALLOW_FINITE_WORKER_DAEMON=1 for a narrow explicit override."
  fi

  if [[ -n "${max_polls}" ]]; then
    if ! _is_integer "${max_polls}"; then
      _die "RTLCP_MAX_POLLS must be an integer when set; got '${max_polls}'."
    fi
    if (( max_polls > 0 )) && [[ "${allow_finite}" != "1" ]]; then
      _die "RTLCP_MAX_POLLS=${max_polls} is not allowed for a managed daemon. Leave it unset for persistent mode or set RTLCP_ALLOW_FINITE_WORKER_DAEMON=1 for a narrow explicit override."
    fi
  fi
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

_preflight() {
  local db_host db_mode role max_polls_display stop_on_no_work allow_finite
  _require_database_url
  _require_machine_key
  _require_venv
  _validate_database_host
  _validate_persistence_settings
  _check_import_path

  db_host="$(_database_host)"
  db_mode="${RTLCP_DB_MODE:-unset}"
  role="${RTLCP_ROLE:-unset}"
  stop_on_no_work="${RTLCP_STOP_ON_NO_WORK:-0}"
  allow_finite="${RTLCP_ALLOW_FINITE_WORKER_DAEMON:-0}"
  if [[ -n "${RTLCP_MAX_POLLS:-}" ]] && _is_integer "${RTLCP_MAX_POLLS}" && (( RTLCP_MAX_POLLS > 0 )); then
    max_polls_display="${RTLCP_MAX_POLLS}"
  else
    max_polls_display="persistent"
  fi

  cat <<EOF
preflight OK
repo_root=${REPO_ROOT}
venv_path=${VENV_PATH}
machine_key=${RTLCP_MACHINE_KEY}
hostname=${RTLCP_HOSTNAME}
role=${role}
db_mode=${db_mode}
db_host=${db_host}
runtime_dir=${RUNTIME_DIR}
pid_dir=${RUNTIME_DIR}
daemon_log_dir=${RUNTIME_DIR}
worker_log_root=${WORKER_LOG_ROOT}
stop_on_no_work=${stop_on_no_work}
max_polls=${max_polls_display}
allow_finite_worker_daemon=${allow_finite}
EOF
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
  local run_preflight
  run_preflight="${1:-1}"
  if [[ "${run_preflight}" == "1" ]]; then
    _preflight
  fi
  mkdir -p "${RUNTIME_DIR}" "${WORKER_LOG_ROOT}"
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
    _preflight
    _stop_all
    _start_all 0
    ;;
  status)
    _status_all
    ;;
  check-import)
    _require_database_url
    _require_venv
    _validate_database_host
    _check_import_path
    ;;
  preflight)
    _preflight
    ;;
  *)
    _usage
    exit 1
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
SERVICE="${2:-}"
DEFAULT_SERVICE_REPO="/workspaces/rtlgen-eval-clean"
SERVICE_REPO_ROOT="${RTLGEN_SERVICE_REPO:-${DEFAULT_SERVICE_REPO}}"

ENSURE_SERVICE_REPO="${REPO_ROOT:-/workspaces/RTLGen}/control_plane/scripts/ensure_service_repo.sh"
RUNTIME_DIR="${RTLCP_RUNTIME_DIR:-/tmp/rtlgen-control-plane}"
mkdir -p "${RUNTIME_DIR}"

case "${SERVICE}" in
  worker)
    TARGET_CMD=("${SERVICE_REPO_ROOT}/control_plane/scripts/run_worker_daemon_service.sh")
    ;;
  completions)
    TARGET_CMD=("${SERVICE_REPO_ROOT}/.devcontainer/run_maintenance_loop.sh")
    ;;
  api)
    TARGET_CMD=("${SERVICE_REPO_ROOT}/control_plane/scripts/run_api_service.sh")
    ;;
  *)
    echo "Unknown service '${SERVICE}'. Expected 'worker', 'completions', or 'api'." >&2
    exit 1
    ;;
esac

PID_FILE="${RUNTIME_DIR}/${SERVICE}.pid"
LOG_FILE="${RUNTIME_DIR}/${SERVICE}.log"

_timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

_is_running() {
  if [[ ! -f "${PID_FILE}" ]]; then
    return 1
  fi
  local pid
  pid="$(cat "${PID_FILE}")"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

_tail_log() {
  if [[ -f "${LOG_FILE}" ]]; then
    tail -n "${1:-40}" "${LOG_FILE}"
  else
    echo "log not found: ${LOG_FILE}"
  fi
}

case "${ACTION}" in
  start)
    "${ENSURE_SERVICE_REPO}"
    if _is_running; then
      echo "${SERVICE} already running: pid=$(cat "${PID_FILE}") log=${LOG_FILE}"
      exit 0
    fi
    rm -f "${PID_FILE}"
    : >"${LOG_FILE}"
    {
      printf '[%s] service=%s action=start\n' "$(_timestamp)" "${SERVICE}"
      printf '[%s] service=%s runtime_dir=%s\n' "$(_timestamp)" "${SERVICE}" "${RUNTIME_DIR}"
      case "${SERVICE}" in
        worker)
          printf '[%s] service=%s machine_key=%s hostname=%s db=%s\n' \
            "$(_timestamp)" "${SERVICE}" "${RTLCP_MACHINE_KEY:-}" "${RTLCP_HOSTNAME:-$(hostname)}" "${RTLCP_DATABASE_URL:-}"
          ;;
        completions)
          printf '[%s] service=%s repo=%s db=%s process_completions=%s\n' \
            "$(_timestamp)" "${SERVICE}" "${RTLCP_REPO_SLUG:-}" "${RTLCP_DATABASE_URL:-}" "${RTLCP_PROCESS_COMPLETIONS_IN_LOOP:-0}"
          ;;
        api)
          printf '[%s] service=%s host=%s port=%s db=%s\n' \
            "$(_timestamp)" "${SERVICE}" "${RTLCP_HOST:-0.0.0.0}" "${RTLCP_PORT:-8080}" "${RTLCP_DATABASE_URL:-}"
          ;;
      esac
    } >>"${LOG_FILE}"
    if command -v setsid >/dev/null 2>&1; then
      setsid "${TARGET_CMD[@]}" </dev/null >>"${LOG_FILE}" 2>&1 &
    else
      nohup "${TARGET_CMD[@]}" </dev/null >>"${LOG_FILE}" 2>&1 &
    fi
    echo "$!" >"${PID_FILE}"
    sleep 0.2
    if ! kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
      rm -f "${PID_FILE}"
      echo "failed to start ${SERVICE}; see ${LOG_FILE}" >&2
      exit 1
    fi
    echo "started ${SERVICE}: pid=$(cat "${PID_FILE}") log=${LOG_FILE}"
    ;;
  stop)
    if ! _is_running; then
      rm -f "${PID_FILE}"
      echo "${SERVICE} not running"
      exit 0
    fi
    kill "$(cat "${PID_FILE}")"
    rm -f "${PID_FILE}"
    echo "stopped ${SERVICE}"
    ;;
  restart)
    "$0" stop "${SERVICE}" || true
    "$0" start "${SERVICE}"
    ;;
  status)
    if _is_running; then
      echo "${SERVICE} running: pid=$(cat "${PID_FILE}") log=${LOG_FILE}"
    else
      rm -f "${PID_FILE}"
      echo "${SERVICE} not running"
      exit 1
    fi
    ;;
  logs)
    _tail_log "${TAIL_LINES:-40}"
    ;;
  *)
    echo "Usage: $0 <start|stop|restart|status|logs> <worker|completions|api>" >&2
    exit 1
    ;;
esac

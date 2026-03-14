#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"
SERVICE="${2:-}"

RUNTIME_DIR="${RTLCP_RUNTIME_DIR:-/tmp/rtlgen-control-plane}"
mkdir -p "${RUNTIME_DIR}"

case "${SERVICE}" in
  worker)
    TARGET_CMD=(/workspaces/RTLGen/control_plane/scripts/run_worker_daemon_service.sh)
    ;;
  completions)
    TARGET_CMD=(/workspaces/RTLGen/.devcontainer/run_completion_loop.sh)
    ;;
  *)
    echo "Unknown service '${SERVICE}'. Expected 'worker' or 'completions'." >&2
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

case "${ACTION}" in
  start)
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
          printf '[%s] service=%s repo=%s db=%s submit=%s\n' \
            "$(_timestamp)" "${SERVICE}" "${RTLCP_REPO_SLUG:-}" "${RTLCP_DATABASE_URL:-}" "${RTLCP_SUBMIT:-0}"
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
  status)
    if _is_running; then
      echo "${SERVICE} running: pid=$(cat "${PID_FILE}") log=${LOG_FILE}"
    else
      echo "${SERVICE} not running"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 <start|stop|status> <worker|completions>" >&2
    exit 1
    ;;
esac

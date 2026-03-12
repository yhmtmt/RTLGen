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
    nohup "${TARGET_CMD[@]}" >>"${LOG_FILE}" 2>&1 &
    echo "$!" >"${PID_FILE}"
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

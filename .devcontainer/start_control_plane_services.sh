#!/usr/bin/env bash
set -euo pipefail

ROLE=${RTLCP_ROLE:-server}
DB_MODE=${RTLCP_DB_MODE:-}
AUTOSTART_WORKER="${RTLCP_AUTOSTART_WORKER_DAEMON:-}"
AUTOSTART_COMPLETIONS="${RTLCP_AUTOSTART_COMPLETIONS:-}"
AUTOSTART_API="${RTLCP_AUTOSTART_API:-}"
AUTOSTART_RESOLVER="${RTLCP_AUTOSTART_RESOLVER:-}"
DEFAULT_DB_URL="postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane"

case "${ROLE}" in
  server)
    DB_MODE="${DB_MODE:-local}"
    ;;
  evaluator)
    DB_MODE="${DB_MODE:-remote}"
    ;;
  *)
    echo "Unknown RTLCP_ROLE='${ROLE}'. Expected 'server' or 'evaluator'." >&2
    exit 1
    ;;
esac

export RTLCP_DB_MODE="${DB_MODE}"

if [[ -z "${RTLCP_DATABASE_URL:-}" ]]; then
  if [[ "${DB_MODE}" == "local" ]]; then
    export RTLCP_DATABASE_URL="${DEFAULT_DB_URL}"
  else
    echo "RTLCP_DATABASE_URL is required when RTLCP_DB_MODE=remote" >&2
    exit 1
  fi
fi

case "${DB_MODE}" in
  local)
    /workspaces/RTLGen/.devcontainer/start_postgres.sh
    echo "Using local PostgreSQL for control-plane DB"
    ;;
  remote)
    echo "Using remote/shared PostgreSQL for control-plane DB: ${RTLCP_DATABASE_URL}"
    ;;
  *)
    echo "Unknown RTLCP_DB_MODE='${DB_MODE}'. Expected 'local' or 'remote'." >&2
    exit 1
    ;;
esac

case "${ROLE}" in
  server)
    echo "Developer/server role is not an execution node; worker/completion stay disabled unless started explicitly"
    echo "Skipping completion loop autostart for server role"
    if [[ "${AUTOSTART_RESOLVER:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start resolver
    else
      echo "Skipping resolver autostart for server role"
    fi
    ;;
  evaluator)
    echo "Evaluator role owns worker and periodic maintenance services for the internal lane"
    echo "Configured worker concurrency: ${RTLCP_WORKER_CONCURRENCY:-1}"
    if [[ "${AUTOSTART_WORKER:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start worker
    else
      echo "Skipping worker daemon autostart for evaluator role"
    fi
    if [[ "${AUTOSTART_COMPLETIONS:-0}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start completions
    else
      echo "Skipping maintenance loop autostart for evaluator role"
    fi
    if [[ "${AUTOSTART_API:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start api
    else
      echo "Skipping control-plane API autostart for evaluator role"
    fi
    if [[ "${AUTOSTART_RESOLVER:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start resolver
    else
      echo "Skipping resolver autostart for evaluator role"
    fi
    ;;
esac

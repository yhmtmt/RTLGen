#!/usr/bin/env bash
set -euo pipefail

ROLE=${RTLCP_ROLE:-server}
AUTOSTART_WORKER="${RTLCP_AUTOSTART_WORKER_DAEMON:-}"
AUTOSTART_COMPLETIONS="${RTLCP_AUTOSTART_COMPLETIONS:-}"

case "${ROLE}" in
  server)
    export RTLCP_DATABASE_URL="${RTLCP_DATABASE_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}"
    /workspaces/RTLGen/.devcontainer/start_postgres.sh
    if [[ "${AUTOSTART_COMPLETIONS:-0}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start completions
    else
      echo "Skipping completion loop autostart for server role"
    fi
    ;;
  evaluator)
    : "${RTLCP_DATABASE_URL:?RTLCP_DATABASE_URL is required for evaluator role}"
    echo "Skipping local PostgreSQL startup for evaluator role"
    if [[ "${AUTOSTART_WORKER:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start worker
    else
      echo "Skipping worker daemon autostart for evaluator role"
    fi
    ;;
  *)
    echo "Unknown RTLCP_ROLE='${ROLE}'. Expected 'server' or 'evaluator'." >&2
    exit 1
    ;;
esac

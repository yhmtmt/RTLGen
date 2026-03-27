#!/usr/bin/env bash
set -euo pipefail

ROLE=${RTLCP_ROLE:-server}
AUTOSTART_WORKER="${RTLCP_AUTOSTART_WORKER_DAEMON:-}"
AUTOSTART_COMPLETIONS="${RTLCP_AUTOSTART_COMPLETIONS:-}"
AUTOSTART_API="${RTLCP_AUTOSTART_API:-}"

case "${ROLE}" in
  server)
    export RTLCP_DATABASE_URL="${RTLCP_DATABASE_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}"
    echo "Skipping local PostgreSQL startup for server role"
    echo "Developer/server role is not an execution node; worker/completion/api stay on evaluator"
    echo "Skipping completion loop autostart for server role"
    ;;
  evaluator)
    export RTLCP_DATABASE_URL="${RTLCP_DATABASE_URL:-postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane}"
    /workspaces/RTLGen/.devcontainer/start_postgres.sh
    echo "Evaluator role owns worker/completion/finalization services for the internal lane"
    echo "Configured worker concurrency: ${RTLCP_WORKER_CONCURRENCY:-1}"
    if [[ "${AUTOSTART_WORKER:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start worker
    else
      echo "Skipping worker daemon autostart for evaluator role"
    fi
    if [[ "${AUTOSTART_COMPLETIONS:-0}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start completions
    else
      echo "Skipping completion loop autostart for evaluator role"
    fi
    if [[ "${AUTOSTART_API:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start api
    else
      echo "Skipping control-plane API autostart for evaluator role"
    fi
    ;;
  *)
    echo "Unknown RTLCP_ROLE='${ROLE}'. Expected 'server' or 'evaluator'." >&2
    exit 1
    ;;
esac

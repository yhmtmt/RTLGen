#!/usr/bin/env bash
set -euo pipefail

ROLE=${RTLCP_ROLE:-server}
DB_MODE=${RTLCP_DB_MODE:-}
AUTOSTART_WORKER="${RTLCP_AUTOSTART_WORKER_DAEMON:-}"
AUTOSTART_COMPLETIONS="${RTLCP_AUTOSTART_COMPLETIONS:-}"
AUTOSTART_API="${RTLCP_AUTOSTART_API:-}"
AUTOSTART_RESOLVER="${RTLCP_AUTOSTART_RESOLVER:-}"
DEFAULT_DB_URL="postgresql+psycopg://rtlgen:rtlgen@localhost:5432/rtlgen_control_plane"
IMAGE_INIT_HELPER="/usr/local/sbin/rtlgen-container-init"
REPO_INIT_HELPER="/workspaces/RTLGen/.devcontainer/rtlgen-container-init"
ORFS_RUNTIME_ROOTS=(
  /orfs/flow/designs/src
  /orfs/flow/designs/nangate45
  /orfs/flow/logs
  /orfs/flow/objects
  /orfs/flow/reports
  /orfs/flow/results
)

prepare_runtime_paths() {
  local path

  if [[ ! -x "${IMAGE_INIT_HELPER}" ]]; then
    echo "Installed container initializer is missing: ${IMAGE_INIT_HELPER}" >&2
    echo "Rebuild the devcontainer image from the current repository source." >&2
    exit 1
  fi
  if [[ ! -f "${REPO_INIT_HELPER}" ]] || ! cmp -s "${IMAGE_INIT_HELPER}" "${REPO_INIT_HELPER}"; then
    echo "Installed container initializer does not match ${REPO_INIT_HELPER}." >&2
    echo "Rebuild the devcontainer image before starting control-plane services." >&2
    exit 1
  fi

  sudo -n "${IMAGE_INIT_HELPER}" prepare
  for path in "${ORFS_RUNTIME_ROOTS[@]}"; do
    if [[ ! -d "${path}" || ! -w "${path}" ]]; then
      echo "OpenROAD runtime path is not writable by uid=$(id -u): ${path}" >&2
      echo "Rebuild the devcontainer image or repair its runtime-path initialization." >&2
      exit 1
    fi
  done
}

prepare_runtime_paths

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
    sudo -n /usr/local/sbin/rtlgen-container-init postgres \
      --role "${RTLCP_DB_ROLE:-rtlgen}" \
      --password "${RTLCP_DB_PASSWORD:-rtlgen}" \
      --database "${RTLCP_DB_NAME:-rtlgen_control_plane}" \
      --version "${RTLCP_PG_VERSION:-14}" \
      --allowed-cidr "${RTLCP_PG_ALLOWED_CIDR:-172.16.0.0/12}"
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
    echo "Developer/server role is not an execution node; worker stays disabled"
    if [[ "${AUTOSTART_COMPLETIONS:-0}" == "1" ]]; then
      export RTLCP_AUTODISPATCH_READY="${RTLCP_AUTODISPATCH_READY:-1}"
      export RTLCP_PROCESS_COMPLETIONS_IN_LOOP="${RTLCP_PROCESS_COMPLETIONS_IN_LOOP:-1}"
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start completions
    else
      echo "Skipping completion loop autostart for server role"
    fi
    if [[ "${AUTOSTART_API:-1}" == "1" ]]; then
      /workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh start api
    else
      echo "Skipping control-plane API autostart for server role"
    fi
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

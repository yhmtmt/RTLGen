#!/usr/bin/env bash
set -euo pipefail

ROLE=${RTLCP_ROLE:-server}

case "${ROLE}" in
  server)
    /workspaces/RTLGen/.devcontainer/start_postgres.sh
    ;;
  evaluator)
    echo "Skipping local PostgreSQL startup for evaluator role"
    ;;
  *)
    echo "Unknown RTLCP_ROLE='${ROLE}'. Expected 'server' or 'evaluator'." >&2
    exit 1
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

ROLE_NAME=${RTLCP_DB_ROLE:-rtlgen}
ROLE_PASSWORD=${RTLCP_DB_PASSWORD:-rtlgen}
DB_NAME=${RTLCP_DB_NAME:-rtlgen_control_plane}

service postgresql start

su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='${ROLE_NAME}'\"" | grep -q 1 || \
  su postgres -c "psql -c \"CREATE ROLE ${ROLE_NAME} LOGIN PASSWORD '${ROLE_PASSWORD}'\""

su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'\"" | grep -q 1 || \
  su postgres -c "createdb -O ${ROLE_NAME} ${DB_NAME}"

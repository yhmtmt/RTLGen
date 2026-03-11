#!/usr/bin/env bash
set -euo pipefail

ROLE_NAME=${RTLCP_DB_ROLE:-rtlgen}
ROLE_PASSWORD=${RTLCP_DB_PASSWORD:-rtlgen}
DB_NAME=${RTLCP_DB_NAME:-rtlgen_control_plane}
PG_VERSION=${RTLCP_PG_VERSION:-14}
ALLOWED_CIDR=${RTLCP_PG_ALLOWED_CIDR:-172.16.0.0/12}
CONF_DIR="/etc/postgresql/${PG_VERSION}/main"
POSTGRES_CONF="${CONF_DIR}/postgresql.conf"
PG_HBA_CONF="${CONF_DIR}/pg_hba.conf"

service postgresql start

if [[ -f "${POSTGRES_CONF}" ]]; then
  sed -i "s/^#\\?listen_addresses\\s*=.*/listen_addresses = '*'/" "${POSTGRES_CONF}"
fi

if [[ -f "${PG_HBA_CONF}" ]]; then
  if ! grep -Fq "host    ${DB_NAME}    ${ROLE_NAME}    ${ALLOWED_CIDR}    scram-sha-256" "${PG_HBA_CONF}"; then
    cat >>"${PG_HBA_CONF}" <<EOF
host    ${DB_NAME}    ${ROLE_NAME}    ${ALLOWED_CIDR}    scram-sha-256
EOF
  fi
fi

service postgresql restart

su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='${ROLE_NAME}'\"" | grep -q 1 || \
  su postgres -c "psql -c \"CREATE ROLE ${ROLE_NAME} LOGIN PASSWORD '${ROLE_PASSWORD}'\""

su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'\"" | grep -q 1 || \
  su postgres -c "createdb -O ${ROLE_NAME} ${DB_NAME}"

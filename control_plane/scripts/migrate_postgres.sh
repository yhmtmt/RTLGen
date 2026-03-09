#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VENV_DIR=${RTLCP_VENV_DIR:-"$ROOT_DIR/.venv"}

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "missing virtualenv at $VENV_DIR; run $ROOT_DIR/scripts/bootstrap_venv.sh first" >&2
  exit 1
fi

if [[ -z "${RTLCP_DATABASE_URL:-}" ]]; then
  echo "RTLCP_DATABASE_URL is required" >&2
  exit 1
fi

if [[ "${RTLCP_DATABASE_URL}" != postgresql+psycopg://* ]]; then
  echo "RTLCP_DATABASE_URL must use the postgresql+psycopg dialect" >&2
  exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$ROOT_DIR"

if [[ -n "${RTLCP_PG_ADMIN_URL:-}" ]]; then
  "$ROOT_DIR/scripts/ensure_postgres_db.sh"
fi

alembic -c alembic.ini upgrade head

python - <<'PY'
from sqlalchemy import create_engine, inspect

from control_plane.config import Settings
from control_plane.models import Base

engine = create_engine(Settings.from_env().database_url, future=True)
tables = sorted(inspect(engine).get_table_names())
expected = sorted(Base.metadata.tables.keys())
missing = [name for name in expected if name not in tables]
if missing:
    raise SystemExit(f"missing tables after PostgreSQL migration: {missing}")
print("OK: alembic upgrade head created expected tables on PostgreSQL")
PY

cat <<EOF
Phase 1 PostgreSQL bring-up passed:
  database_url: $RTLCP_DATABASE_URL
EOF

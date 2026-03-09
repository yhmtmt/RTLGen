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

if [[ -z "${RTLCP_PG_ADMIN_URL:-}" ]]; then
  echo "RTLCP_PG_ADMIN_URL is required to create/check the target PostgreSQL database" >&2
  exit 1
fi

source "$VENV_DIR/bin/activate"

python - <<'PY'
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

admin_url = make_url(__import__("os").environ["RTLCP_PG_ADMIN_URL"])
target_url = make_url(__import__("os").environ["RTLCP_DATABASE_URL"])

if not target_url.database:
    raise SystemExit("target database name is empty in RTLCP_DATABASE_URL")

engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
db_name = target_url.database

with engine.connect() as conn:
    exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}).scalar()
    if not exists:
        quoted = '"' + db_name.replace('"', '""') + '"'
        conn.execute(text(f"CREATE DATABASE {quoted}"))
        print(f"created database: {db_name}")
    else:
        print(f"database already exists: {db_name}")
PY

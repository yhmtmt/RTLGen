#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VENV_DIR=${RTLCP_VENV_DIR:-"$ROOT_DIR/.venv"}
DB_PATH=${RTLCP_SMOKE_DB_PATH:-/tmp/rtlgen-control-plane-phase1.db}
DB_URL=${RTLCP_DATABASE_URL:-"sqlite+pysqlite:///$DB_PATH"}

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "missing virtualenv at $VENV_DIR; run $ROOT_DIR/scripts/bootstrap_venv.sh first" >&2
  exit 1
fi

source "$VENV_DIR/bin/activate"
cd "$ROOT_DIR"

rm -f "$DB_PATH"
export RTLCP_DATABASE_URL="$DB_URL"

alembic -c alembic.ini upgrade head

python - <<'PY'
from sqlalchemy import create_engine, inspect

from control_plane.models import Base

from control_plane.config import Settings

engine = create_engine(Settings.from_env().database_url, future=True)
tables = sorted(inspect(engine).get_table_names())
expected = sorted(Base.metadata.tables.keys())
missing = [name for name in expected if name not in tables]
if missing:
    raise SystemExit(f"missing tables after migration: {missing}")
print("OK: alembic upgrade head created expected tables")
PY

cat <<EOF
Phase 1 migration smoke passed:
  database_url: $DB_URL
EOF

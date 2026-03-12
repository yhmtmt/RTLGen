#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  sql_select.sh --query 'select ...'
  sql_select.sh --file path/to/query.sql

Environment:
  RTLCP_DATABASE_URL   SQLAlchemy-style URL or libpq URL for PostgreSQL
  PSQL_URL             Optional libpq URL override
EOF
}

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 2
fi

mode="$1"
arg="$2"
shift 2

if [[ $# -ne 0 ]]; then
  usage >&2
  exit 2
fi

case "$mode" in
  --query)
    sql="$arg"
    ;;
  --file)
    if [[ ! -f "$arg" ]]; then
      echo "ERROR: query file not found: $arg" >&2
      exit 2
    fi
    sql="$(cat "$arg")"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

trim_sql() {
  python3 - "$1" <<'PY'
import re
import sys

text = sys.argv[1]
text = text.lstrip()
while True:
    if text.startswith("--"):
        nl = text.find("\n")
        text = "" if nl == -1 else text[nl + 1 :].lstrip()
        continue
    if text.startswith("/*"):
        end = text.find("*/")
        if end == -1:
            break
        text = text[end + 2 :].lstrip()
        continue
    break
print(text, end="")
PY
}

normalized="$(trim_sql "$sql")"
lowered="$(printf '%s' "$normalized" | tr '[:upper:]' '[:lower:]')"

case "$lowered" in
  select*|with*|explain\ select*|explain\ with*)
    ;;
  *)
    echo "ERROR: only read-only SELECT/WITH/EXPLAIN queries are allowed" >&2
    exit 2
    ;;
esac

db_url="${PSQL_URL:-${RTLCP_DATABASE_URL:-}}"
if [[ -z "$db_url" ]]; then
  echo "ERROR: set PSQL_URL or RTLCP_DATABASE_URL" >&2
  exit 2
fi

# Convert SQLAlchemy psycopg URLs into libpq URLs accepted by psql.
db_url="${db_url/postgresql+psycopg:/postgresql:}"
db_url="${db_url/postgresql+psycopg2:/postgresql:}"

exec psql "$db_url" -v ON_ERROR_STOP=1 -P pager=off -c "$sql"

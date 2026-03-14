#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -z "${RTLCP_DATABASE_URL:-}" ]]; then
  echo "ERROR: RTLCP_DATABASE_URL is required" >&2
  exit 2
fi

if [[ -d "$REPO_ROOT/control_plane/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/control_plane/.venv/bin/activate"
fi

export PYTHONPATH="$REPO_ROOT/control_plane${PYTHONPATH:+:$PYTHONPATH}"

python3 -m control_plane.cli.main operator-status \
  --database-url "$RTLCP_DATABASE_URL" \
  "$@"

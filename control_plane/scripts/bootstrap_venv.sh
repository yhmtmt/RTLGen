#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VENV_DIR=${1:-"$ROOT_DIR/.venv"}

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -e "$ROOT_DIR[test]"
python -m pip install "psycopg[binary]>=3.2"
python -m pip install "PyYAML>=6.0"

cat <<EOF
control_plane virtualenv ready:
  venv: $VENV_DIR

activate with:
  source "$VENV_DIR/bin/activate"

next recommended step:
  "$ROOT_DIR/scripts/migrate_smoke.sh"
EOF

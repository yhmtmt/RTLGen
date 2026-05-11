#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -d "$REPO_ROOT/control_plane/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/control_plane/.venv/bin/activate"
fi

export PYTHONPATH="$REPO_ROOT/control_plane${PYTHONPATH:+:$PYTHONPATH}"

python3 -m control_plane.cli.main request-evaluator-refresh \
  --repo "${RTLCP_GITHUB_REPO:-yhmtmt/RTLGen}" \
  --repo-root "$REPO_ROOT" \
  "$@"

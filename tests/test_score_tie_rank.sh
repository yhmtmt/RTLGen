#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_score_tie_rank.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

grep -q "module score_tie_rank_r4_s16_l16" score_tie_rank_r4_s16_l16.v
grep -q "score_i == best_score" score_tie_rank_r4_s16_l16.v

iverilog -g2012 -s score_tie_rank_tb -o sim score_tie_rank_r4_s16_l16.v "$ROOT/tests/score_tie_rank_tb.v"
vvp sim

WRAP_DIR="$TMP/wrapper"
mkdir -p "$WRAP_DIR"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_score_tie_rank.json" "$WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path

from generate_design import generate_wrapper, identify_design

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
design = identify_design(config)
assert design["kind"] == "score_tie_rank"
generate_wrapper(config, sys.argv[2], design)
PY
iverilog -g2012 -s score_tie_rank_r4_s16_l16_wrapper -t null \
  score_tie_rank_r4_s16_l16.v "$WRAP_DIR/score_tie_rank_r4_s16_l16_wrapper.v"

cat > "$TMP/sweep.json" <<'JSON'
{
  "tag_prefix": "score_tie_rank_dryrun",
  "flow_params": {
    "CLOCK_PERIOD": [10.0]
  }
}
JSON
python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_score_tie_rank.json" \
  --platform nangate45 \
  --sweep "$TMP/sweep.json" \
  --out_root "$TMP/runs" \
  --dry_run
popd >/dev/null

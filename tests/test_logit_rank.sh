#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_logit_rank.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

grep -q "module logit_rank_r4_l16_k2" logit_rank_r4_l16_k2.v
grep -q "logit_i > top_logit_k" logit_rank_r4_l16_k2.v

iverilog -g2012 -s logit_rank_tb -o sim logit_rank_r4_l16_k2.v "$ROOT/tests/logit_rank_tb.v"
vvp sim

WRAP_DIR="$TMP/wrapper"
mkdir -p "$WRAP_DIR"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_logit_rank.json" "$WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path

from generate_design import generate_wrapper, identify_design

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
design = identify_design(config)
assert design["kind"] == "logit_rank"
assert design["top_k"] == 2
generate_wrapper(config, sys.argv[2], design)
PY
iverilog -g2012 -s logit_rank_r4_l16_k2_wrapper -t null \
  logit_rank_r4_l16_k2.v "$WRAP_DIR/logit_rank_r4_l16_k2_wrapper.v"

cat > "$TMP/sweep.json" <<'JSON'
{
  "tag_prefix": "logit_rank_dryrun",
  "flow_params": {
    "CLOCK_PERIOD": [10.0]
  }
}
JSON
python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_logit_rank.json" \
  --platform nangate45 \
  --sweep "$TMP/sweep.json" \
  --out_root "$TMP/runs" \
  --dry_run

for cfg in \
  "$ROOT/runs/designs/activations/logit_rank_r8_l16_k1_wrapper/config_logit_rank_r8_l16_k1.json" \
  "$ROOT/runs/designs/activations/logit_rank_r8_l16_k4_wrapper/config_logit_rank_r8_l16_k4.json"; do
  cfg_name="$(basename "$cfg" .json)"
  cfg_tmp="$TMP/$cfg_name"
  mkdir -p "$cfg_tmp/wrapper"
  cp "$cfg" "$cfg_tmp/config.json"
  (
    cd "$cfg_tmp"
    "$ROOT/build/rtlgen" config.json
  )
  module_name="$(python3 -c "import json; print(json.load(open('$cfg'))['operations'][0]['module_name'])")"
  PYTHONPATH="$ROOT/scripts" python3 - "$cfg" "$cfg_tmp/wrapper" <<'PY'
import json
import sys
from pathlib import Path

from generate_design import generate_wrapper, identify_design

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
design = identify_design(config)
generate_wrapper(config, sys.argv[2], design)
PY
  iverilog -g2012 -s "${module_name}_wrapper" -t null \
    "$cfg_tmp/${module_name}.v" "$cfg_tmp/wrapper/${module_name}_wrapper.v"
done
popd >/dev/null

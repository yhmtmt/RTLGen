#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_attention_kv_reducer.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

grep -q "module attention_kv_reducer_p3_l4_v8_s12_a16" attention_kv_reducer_p3_l4_v8_s12_a16.v
grep -q "Attention/KV cross-tile reducer primitive" attention_kv_reducer_p3_l4_v8_s12_a16.v
grep -q "accepted_partial_count" attention_kv_reducer_p3_l4_v8_s12_a16.v
grep -q "final_completion_cycle" attention_kv_reducer_p3_l4_v8_s12_a16.v

YOSYS_BIN="${YOSYS_BIN:-}"
if [[ -z "$YOSYS_BIN" ]]; then
  if command -v yosys >/dev/null 2>&1; then
    YOSYS_BIN="$(command -v yosys)"
  elif [[ -x /oss-cad-suite/bin/yosys ]]; then
    YOSYS_BIN=/oss-cad-suite/bin/yosys
  fi
fi
if [[ -n "$YOSYS_BIN" ]]; then
  "$YOSYS_BIN" -q -p "read_verilog attention_kv_reducer_p3_l4_v8_s12_a16.v; hierarchy -top attention_kv_reducer_p3_l4_v8_s12_a16; proc"
fi

iverilog -g2012 -s attention_kv_reducer_tb -o sim \
  attention_kv_reducer_p3_l4_v8_s12_a16.v "$ROOT/tests/attention_kv_reducer_tb.v"
vvp sim

WRAP_DIR="$TMP/wrapper"
mkdir -p "$WRAP_DIR"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_attention_kv_reducer.json" "$WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path

from generate_design import generate_wrapper, identify_design

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
design = identify_design(config)
assert design["kind"] == "attention_kv_reducer"
assert design["value_width"] == 32
assert design["reduced_value_width"] == 64
generate_wrapper(config, sys.argv[2], design)
PY
iverilog -g2012 -s attention_kv_reducer_p3_l4_v8_s12_a16_wrapper -t null \
  attention_kv_reducer_p3_l4_v8_s12_a16.v \
  "$WRAP_DIR/attention_kv_reducer_p3_l4_v8_s12_a16_wrapper.v"

python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_attention_kv_reducer.json" \
  --platform nangate45 \
  --sweep "$ROOT/runs/campaigns/activations/attention_kv_reducer/sweeps/nangate45_macro_smoke.json" \
  --out_root "$TMP/runs" \
  --dry_run
popd >/dev/null

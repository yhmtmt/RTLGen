#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cp "$ROOT/examples/config_attention_kv_reducer_tree.json" "$TMP/config.json"
cd "$TMP"

"$ROOT/build/rtlgen" "$TMP/config.json"
grep -q "module attention_kv_reducer_tree_p4_l4_v8_s12_a16" attention_kv_reducer_tree_p4_l4_v8_s12_a16.v
grep -q "Registered binary tree reducer" attention_kv_reducer_tree_p4_l4_v8_s12_a16.v
grep -q "accepted_group_count" attention_kv_reducer_tree_p4_l4_v8_s12_a16.v
grep -q "final_completion_cycle" attention_kv_reducer_tree_p4_l4_v8_s12_a16.v

YOSYS_BIN="${YOSYS_BIN:-}"
if [[ -z "$YOSYS_BIN" ]]; then
  if command -v yosys >/dev/null 2>&1; then
    YOSYS_BIN="yosys"
  elif [[ -x /oss-cad-suite/bin/yosys ]]; then
    YOSYS_BIN="/oss-cad-suite/bin/yosys"
  fi
fi
if [[ -n "$YOSYS_BIN" ]]; then
  "$YOSYS_BIN" -q -p "read_verilog attention_kv_reducer_tree_p4_l4_v8_s12_a16.v; hierarchy -top attention_kv_reducer_tree_p4_l4_v8_s12_a16; proc"
fi

iverilog -g2012 -s attention_kv_reducer_tree_tb -o sim \
  attention_kv_reducer_tree_p4_l4_v8_s12_a16.v "$ROOT/tests/attention_kv_reducer_tree_tb.v"
vvp sim

WRAP_DIR="$TMP/wrap"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_attention_kv_reducer_tree.json" "$WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path
import generate_design

cfg = json.loads(Path(sys.argv[1]).read_text())
design = generate_design.identify_design(cfg)
assert design["kind"] == "attention_kv_reducer_tree"
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
generate_design.generate_wrapper(cfg, str(out), design)
PY
iverilog -g2012 -s attention_kv_reducer_tree_p4_l4_v8_s12_a16_wrapper -t null \
  attention_kv_reducer_tree_p4_l4_v8_s12_a16.v \
  "$WRAP_DIR/attention_kv_reducer_tree_p4_l4_v8_s12_a16_wrapper.v"

python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_attention_kv_reducer_tree.json" \
  --platform nangate45 \
  --sweep "$ROOT/runs/campaigns/activations/attention_kv_reducer_tree/sweeps/nangate45_macro_frontier.json" \
  --dry_run

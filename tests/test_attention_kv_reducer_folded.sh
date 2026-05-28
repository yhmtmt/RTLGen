#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cp "$ROOT/examples/config_attention_kv_reducer_folded.json" "$TMP/config.json"
cd "$TMP"

"$ROOT/build/rtlgen" "$TMP/config.json"
grep -q "module attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16" attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v
grep -q "Folded attention/KV reducer" attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v
grep -q "PARTIALS_PER_CYCLE = 2" attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v
grep -q "accepted_chunk_count" attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v

YOSYS_BIN="${YOSYS_BIN:-}"
if [[ -z "$YOSYS_BIN" ]]; then
  if command -v yosys >/dev/null 2>&1; then
    YOSYS_BIN="yosys"
  elif [[ -x /oss-cad-suite/bin/yosys ]]; then
    YOSYS_BIN="/oss-cad-suite/bin/yosys"
  fi
fi
if [[ -n "$YOSYS_BIN" ]]; then
  "$YOSYS_BIN" -q -p "read_verilog attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v; hierarchy -top attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16; proc"
fi

iverilog -g2012 -s attention_kv_reducer_folded_tb -o sim \
  attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v "$ROOT/tests/attention_kv_reducer_folded_tb.v"
vvp sim

WRAP_DIR="$TMP/wrap"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_attention_kv_reducer_folded.json" "$WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path
import generate_design

cfg = json.loads(Path(sys.argv[1]).read_text())
design = generate_design.identify_design(cfg)
assert design["kind"] == "attention_kv_reducer_folded"
assert design["value_width"] == 64
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
generate_design.generate_wrapper(cfg, str(out), design)
PY
iverilog -g2012 -s attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16_wrapper -t null \
  attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16.v \
  "$WRAP_DIR/attention_kv_reducer_folded_p4_ppc2_l4_v8_s12_a16_wrapper.v"

python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_attention_kv_reducer_folded.json" \
  --platform nangate45 \
  --sweep "$ROOT/runs/campaigns/activations/attention_kv_reducer_folded/sweeps/nangate45_macro_frontier.json" \
  --dry_run

SRC_TMP="$TMP/internal_source"
mkdir -p "$SRC_TMP"
cp "$ROOT/examples/config_attention_kv_reducer_folded_internal_source.json" "$SRC_TMP/config.json"
(
  cd "$SRC_TMP"
  "$ROOT/build/rtlgen" "$SRC_TMP/config.json"
)

SRC_WRAP_DIR="$TMP/internal_source_wrap"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_attention_kv_reducer_folded_internal_source.json" "$SRC_WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path
import generate_design

cfg = json.loads(Path(sys.argv[1]).read_text())
design = generate_design.identify_design(cfg)
assert design["kind"] == "attention_kv_reducer_folded_internal_source"
assert design["value_width"] == 64
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
generate_design.generate_wrapper(cfg, str(out), design)
wrapper = out / "attention_kv_reducer_folded_src_p4_ppc2_l4_v8_s12_a16_wrapper.v"
text = wrapper.read_text()
port_header = text.split(");", 1)[0]
assert "input [63:0] value_fragments" not in port_header
assert "input [47:0] stat_fragments" not in port_header
assert "wire [VALUE_WIDTH-1:0] value_fragments" in text
assert "assign partial_valid = 1'b1" in text
PY
iverilog -g2012 -s attention_kv_reducer_folded_src_p4_ppc2_l4_v8_s12_a16_wrapper -t null \
  "$SRC_TMP/attention_kv_reducer_folded_src_p4_ppc2_l4_v8_s12_a16.v" \
  "$SRC_WRAP_DIR/attention_kv_reducer_folded_src_p4_ppc2_l4_v8_s12_a16_wrapper.v"

python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/runs/designs/activations/attention_kv_reducer_folded_src_p8_ppc4_l16_v16_s16_a24_wrapper/config_attention_kv_reducer_folded_src_p8_ppc4_l16_v16_s16_a24.json" \
  --platform nangate45 \
  --sweep "$ROOT/runs/campaigns/activations/attention_kv_reducer_folded/sweeps/nangate45_macro_internal_source.json" \
  --dry_run

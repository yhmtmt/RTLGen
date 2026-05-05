#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_candidate_stream_merge_fifo.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

grep -q "module candidate_stream_merge_fifo_k2_l16_t8_d2" candidate_stream_merge_fifo_k2_l16_t8_d2.v
grep -q "CandidateStream ready-valid merger" candidate_stream_merge_fifo_k2_l16_t8_d2.v
grep -q "producer_stall_cycles" candidate_stream_merge_fifo_k2_l16_t8_d2.v
grep -q "final_completion_cycle" candidate_stream_merge_fifo_k2_l16_t8_d2.v

YOSYS_BIN="${YOSYS_BIN:-}"
if [[ -z "$YOSYS_BIN" ]]; then
  if command -v yosys >/dev/null 2>&1; then
    YOSYS_BIN="$(command -v yosys)"
  elif [[ -x /oss-cad-suite/bin/yosys ]]; then
    YOSYS_BIN=/oss-cad-suite/bin/yosys
  fi
fi
if [[ -n "$YOSYS_BIN" ]]; then
  "$YOSYS_BIN" -q -p "read_verilog candidate_stream_merge_fifo_k2_l16_t8_d2.v; hierarchy -top candidate_stream_merge_fifo_k2_l16_t8_d2; proc"
fi

iverilog -g2012 -s candidate_stream_merge_fifo_tb -o sim \
  candidate_stream_merge_fifo_k2_l16_t8_d2.v "$ROOT/tests/candidate_stream_merge_fifo_tb.v"
vvp sim

WRAP_DIR="$TMP/wrapper"
mkdir -p "$WRAP_DIR"
PYTHONPATH="$ROOT/scripts" python3 - "$ROOT/examples/config_candidate_stream_merge_fifo.json" "$WRAP_DIR" <<'PY'
import json
import sys
from pathlib import Path

from generate_design import generate_wrapper, identify_design

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
design = identify_design(config)
assert design["kind"] == "candidate_stream_merge_fifo"
assert design["top_k"] == 2
generate_wrapper(config, sys.argv[2], design)
PY
iverilog -g2012 -s candidate_stream_merge_fifo_k2_l16_t8_d2_wrapper -t null \
  candidate_stream_merge_fifo_k2_l16_t8_d2.v \
  "$WRAP_DIR/candidate_stream_merge_fifo_k2_l16_t8_d2_wrapper.v"

cat > "$TMP/sweep.json" <<'JSON'
{
  "tag_prefix": "candidate_stream_merge_fifo_dryrun",
  "flow_params": {
    "CLOCK_PERIOD": [10.0]
  }
}
JSON
python3 "$ROOT/scripts/run_sweep.py" \
  --configs "$ROOT/examples/config_candidate_stream_merge_fifo.json" \
  --platform nangate45 \
  --sweep "$TMP/sweep.json" \
  --out_root "$TMP/runs" \
  --dry_run
popd >/dev/null

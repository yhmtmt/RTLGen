#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_softmax_rowwise_int8.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

python3 "$ROOT/scripts/softmax_rowwise_ref.py" --config config.json --row 0,0,0,0 > ref0.json
python3 "$ROOT/scripts/softmax_rowwise_ref.py" --config config.json --row 4,0,0,0 > ref1.json
python3 "$ROOT/scripts/softmax_rowwise_ref.py" --config config.json --row=-4,0,4,8 > ref2.json

python3 - <<'PY'
import json
from pathlib import Path

expected = [
    [32, 32, 32, 32],
    [107, 7, 7, 7],
    [1, 1, 7, 118],
]
for idx, exp in enumerate(expected):
    payload = json.loads(Path(f"ref{idx}.json").read_text(encoding="utf-8"))
    got = payload["rows"][0]["output"]
    if got != exp:
        raise SystemExit(f"reference mismatch idx={idx} got={got} expected={exp}")
PY

iverilog -g2012 -s softmax_rowwise_tb -o sim softmax_rowwise_int8_r4.v "$ROOT/tests/softmax_rowwise_tb.v"
vvp sim
popd >/dev/null

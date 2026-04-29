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

python3 - <<'PY'
import json
from pathlib import Path

cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
opts = cfg["operations"][0]["options"]
opts["normalization_mode"] = "reciprocal_quantized"
opts["reciprocal_bits"] = 10
Path("config_recip_q10.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
PY
"$ROOT/build/rtlgen" config_recip_q10.json
if grep -q " / sum_weights" softmax_rowwise_int8_r4.v; then
  echo "reciprocal_quantized softmax emitted divider" >&2
  exit 1
fi
python3 "$ROOT/scripts/softmax_rowwise_ref.py" --config config_recip_q10.json --row=-4,0,4,8 > ref_recip.json
python3 - <<'PY'
import json
from pathlib import Path

got = json.loads(Path("ref_recip.json").read_text(encoding="utf-8"))["rows"][0]["output"]
expected = [1, 1, 7, 118]
if got != expected:
    raise SystemExit(f"reciprocal reference mismatch got={got} expected={expected}")
PY
iverilog -g2012 -s softmax_rowwise_tb -o sim_recip softmax_rowwise_int8_r4.v "$ROOT/tests/softmax_rowwise_tb.v"
vvp sim_recip
popd >/dev/null

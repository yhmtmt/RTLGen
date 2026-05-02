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
opts["reciprocal_lut_bucket_shift"] = 4
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
expected = [1, 1, 7, 113]
if got != expected:
    raise SystemExit(f"reciprocal reference mismatch got={got} expected={expected}")
PY
iverilog -g2012 -DSOFTMAX_RECIP_Q10_BUCKETED -s softmax_rowwise_tb -o sim_recip softmax_rowwise_int8_r4.v "$ROOT/tests/softmax_rowwise_tb.v"
vvp sim_recip

python3 - <<'PY'
import json
from pathlib import Path

cfg = {
    "version": "1.1",
    "operands": [{"name": "logits", "dimensions": 1, "bit_width": 12, "signed": True}],
    "operations": [
        {
            "type": "softmax_rowwise",
            "module_name": "softmax_rowwise_q12_pwl_r4",
            "operand": "logits",
            "options": {
                "impl": "pwl_exp",
                "row_elems": 4,
                "input_frac_bits": 8,
                "weight_bits": 12,
                "accum_bits": 28,
                "output_scale": 4095,
                "normalization_mode": "exact",
            },
        }
    ],
}
Path("config_q12_pwl.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
PY
"$ROOT/build/rtlgen" config_q12_pwl.json
python3 "$ROOT/scripts/softmax_rowwise_ref.py" --config config_q12_pwl.json --row 0,0,0,0 --row 0,-512,-1024,-2048 > ref_q12_pwl.json
python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("ref_q12_pwl.json").read_text(encoding="utf-8"))
expected = [[1024, 1024, 1024, 1024], [3549, 480, 65, 1]]
got = [row["output"] for row in payload["rows"]]
if got != expected:
    raise SystemExit(f"q12 PWL reference mismatch got={got} expected={expected}")
PY
iverilog -g2012 -s softmax_rowwise_q12_pwl_tb -o sim_q12_pwl softmax_rowwise_q12_pwl_r4.v "$ROOT/tests/softmax_rowwise_q12_pwl_tb.v"
vvp sim_q12_pwl

python3 - <<'PY'
import json
from pathlib import Path

cfg = json.loads(Path("config_q12_pwl.json").read_text(encoding="utf-8"))
opts = cfg["operations"][0]["options"]
opts["normalization_mode"] = "reciprocal_quantized"
opts["reciprocal_bits"] = 12
opts["reciprocal_lut_bucket_shift"] = 8
Path("config_q12_pwl_recip_q12_bucket8.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
PY
"$ROOT/build/rtlgen" config_q12_pwl_recip_q12_bucket8.json
if grep -q " / sum_weights" softmax_rowwise_q12_pwl_r4.v; then
  echo "q12 PWL reciprocal_quantized softmax emitted divider" >&2
  exit 1
fi
python3 "$ROOT/scripts/softmax_rowwise_ref.py" --config config_q12_pwl_recip_q12_bucket8.json --row 0,0,0,0 --row 0,-512,-1024,-2048 > ref_q12_pwl_recip.json
python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("ref_q12_pwl_recip.json").read_text(encoding="utf-8"))
expected = [[1024, 1024, 1024, 1024], [3447, 466, 63, 1]]
got = [row["output"] for row in payload["rows"]]
if got != expected:
    raise SystemExit(f"q12 PWL reciprocal reference mismatch got={got} expected={expected}")
PY
iverilog -g2012 -DSOFTMAX_Q12_PWL_RECIP_Q12_BUCKET8 -s softmax_rowwise_q12_pwl_tb -o sim_q12_pwl_recip softmax_rowwise_q12_pwl_r4.v "$ROOT/tests/softmax_rowwise_q12_pwl_tb.v"
vvp sim_q12_pwl_recip
popd >/dev/null

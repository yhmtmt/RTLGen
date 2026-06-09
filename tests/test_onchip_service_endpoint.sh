#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

iverilog -g2012 -s onchip_service_endpoint_tb -o "$TMP/sim" \
  "$ROOT/npu/sim/rtl/onchip_service_endpoint.sv" \
  "$ROOT/tests/onchip_service_endpoint_tb.v"
vvp "$TMP/sim" | tee "$TMP/out.log"

python3 - "$TMP/out.log" <<'PY'
import re
import sys
from pathlib import Path


def reference_locality_first(beats, banks):
    queues = [[] for _ in range(banks)]
    for beat in beats:
        queues[beat["bank"]].append(beat)

    preferred = 0
    emitted = []
    while any(queues):
        if not queues[preferred]:
            for offset in range(1, banks + 1):
                candidate = (preferred + offset) % banks
                if queues[candidate]:
                    preferred = candidate
                    break
        emitted.append(queues[preferred].pop(0))
    return emitted


text = Path(sys.argv[1]).read_text(encoding="utf-8")
out_re = re.compile(r"OUT index=(\d+) bank=(\d+) data=(\d+) last=(\d+) cycle=(\d+)")
observed = []
for match in out_re.finditer(text):
    observed.append(
        {
            "index": int(match.group(1)),
            "bank": int(match.group(2)),
            "data": int(match.group(3)),
            "last": int(match.group(4)),
            "cycle": int(match.group(5)),
        }
    )

input_beats = [
    {"bank": 0, "data": 10, "last": 0},
    {"bank": 1, "data": 20, "last": 0},
    {"bank": 0, "data": 11, "last": 0},
    {"bank": 1, "data": 21, "last": 0},
    {"bank": 2, "data": 30, "last": 1},
]
expected = reference_locality_first(input_beats, banks=4)

observed_order = [(beat["bank"], beat["data"], beat["last"]) for beat in observed]
expected_order = [(beat["bank"], beat["data"], beat["last"]) for beat in expected]
if observed_order != expected_order:
    raise SystemExit(f"locality-first order mismatch: observed={observed_order} expected={expected_order}")
if [beat["index"] for beat in observed] != list(range(len(expected))):
    raise SystemExit(f"non-contiguous output indices: {observed}")
if not all(a["cycle"] < b["cycle"] for a, b in zip(observed, observed[1:])):
    raise SystemExit(f"output cycles are not monotonic: {observed}")

summary = re.search(
    r"SUMMARY accepted=(\d+) emitted=(\d+) producer_stalls=(\d+) "
    r"consumer_stalls=(\d+) endpoint_max=(\d+) bank_max=(\d+) final_cycle=(\d+)",
    text,
)
if not summary:
    raise SystemExit("missing SUMMARY line")
accepted, emitted, producer_stalls, consumer_stalls, endpoint_max, bank_max, final_cycle = (
    int(value) for value in summary.groups()
)
if (accepted, emitted) != (5, 5):
    raise SystemExit(f"unexpected beat counts: accepted={accepted} emitted={emitted}")
if producer_stalls < 1 or consumer_stalls < 1:
    raise SystemExit(
        "expected both producer and consumer backpressure counters to move: "
        f"producer={producer_stalls} consumer={consumer_stalls}"
    )
if endpoint_max != 4 or bank_max != 2:
    raise SystemExit(f"unexpected occupancy maxima: endpoint={endpoint_max} bank={bank_max}")
if final_cycle != observed[-1]["cycle"]:
    raise SystemExit(f"final cycle {final_cycle} did not match final output {observed[-1]}")
if "PASS onchip_service_endpoint" not in text:
    raise SystemExit("testbench did not print PASS")
PY

YOSYS_BIN="${YOSYS_BIN:-}"
if [[ -z "$YOSYS_BIN" ]]; then
  if command -v yosys >/dev/null 2>&1; then
    YOSYS_BIN="$(command -v yosys)"
  elif [[ -x /oss-cad-suite/bin/yosys ]]; then
    YOSYS_BIN=/oss-cad-suite/bin/yosys
  fi
fi
if [[ -n "$YOSYS_BIN" ]]; then
  "$YOSYS_BIN" -q -p "read_verilog -sv $ROOT/npu/sim/rtl/onchip_service_endpoint.sv; hierarchy -top onchip_service_endpoint; proc"
fi

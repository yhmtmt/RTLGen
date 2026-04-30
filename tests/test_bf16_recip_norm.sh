#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_bf16_recip_norm.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json

grep -q "module bf16_recip_norm_r4" bf16_recip_norm_r4.v
grep -q "function \\[RECIP_VALUE_BITS-1:0\\] recip_lut" bf16_recip_norm_r4.v
if grep -q " / " bf16_recip_norm_r4.v; then
  echo "bf16_recip_norm emitted a divider" >&2
  exit 1
fi

iverilog -g2012 -s bf16_recip_norm_tb -o sim bf16_recip_norm_r4.v "$ROOT/tests/bf16_recip_norm_tb.v"
vvp sim
popd >/dev/null

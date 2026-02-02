#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
export FLOPOCO_BIN="${FLOPOCO_BIN:-$ROOT/third_party/flopoco-install/bin/flopoco}"

cp "$ROOT/examples/config_fp_mul.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json
iverilog -g2012 -s fp_mul_tb -o sim fp32_mul.v "$ROOT/tests/fp_mul_tb.v"
vvp sim
popd >/dev/null

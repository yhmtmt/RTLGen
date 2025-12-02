#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_fp_add.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json
iverilog -g2012 -s fp_add_tb -o sim fp32_add.v "$ROOT/tests/fp_add_tb.v"
vvp sim
popd >/dev/null

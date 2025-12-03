#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_activation_fp.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json
iverilog -g2012 -s activation_fp_tb -o sim relu_fp32.v leakyrelu_fp32.v "$ROOT/tests/activation_fp_tb.v"
vvp sim
popd >/dev/null

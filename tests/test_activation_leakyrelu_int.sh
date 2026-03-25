#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_activation_leakyrelu_int8.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json
iverilog -g2012 -s activation_leakyrelu_int_tb -o sim leakyrelu_int8.v "$ROOT/tests/activation_leakyrelu_int_tb.v"
vvp sim
popd >/dev/null

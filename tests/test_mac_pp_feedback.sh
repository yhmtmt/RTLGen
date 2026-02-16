#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

cp "$ROOT/examples/config_mac_pp_feedback.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json
iverilog -g2012 -s mac_pp_feedback_tb -o sim int8_mac_pp_feedback.v MG_CPA.v "$ROOT/tests/mac_pp_feedback_tb.v"
vvp sim
popd >/dev/null

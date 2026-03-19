#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT
if [[ -z "${FLOPOCO_BIN:-}" ]]; then
    if [[ -x "$ROOT/bin/flopoco" ]]; then
        export FLOPOCO_BIN="$ROOT/bin/flopoco"
    elif command -v flopoco >/dev/null 2>&1; then
        export FLOPOCO_BIN="$(command -v flopoco)"
    else
        export FLOPOCO_BIN="$ROOT/third_party/flopoco-install/bin/flopoco"
    fi
fi

cp "$ROOT/examples/config_fp_mac.json" "$TMP/config.json"

pushd "$TMP" >/dev/null
"$ROOT/build/rtlgen" config.json
iverilog -g2012 -s fp_mac_tb -o sim fp32_mac.v "$ROOT/tests/fp_mac_tb.v"
vvp sim
popd >/dev/null

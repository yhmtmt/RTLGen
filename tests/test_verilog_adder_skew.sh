#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
RTLGEN_BIN="${BUILD_DIR}/rtlgen"

if [[ ! -x "${RTLGEN_BIN}" ]]; then
  echo "rtlgen binary not found at ${RTLGEN_BIN}" >&2
  exit 1
fi

pushd "${BUILD_DIR}" >/dev/null
./rtlgen "${ROOT_DIR}/examples/config_adder_skew.json"
popd >/dev/null

iverilog -g2012 -o "${BUILD_DIR}/skewprefix_adder8_tb" \
  "${ROOT_DIR}/tests/adder_skew_tb.v" \
  "${BUILD_DIR}/skewprefix_adder8.v"
vvp "${BUILD_DIR}/skewprefix_adder8_tb"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build"
RTLGEN_BIN="${BUILD_DIR}/rtlgen"

if [[ ! -x "${RTLGEN_BIN}" ]]; then
  echo "rtlgen binary not found at ${RTLGEN_BIN}" >&2
  exit 1
fi

rm -f "${BUILD_DIR}/fir3_mcm.v" "${BUILD_DIR}/dct4_cmvm.v"

pushd "${BUILD_DIR}" >/dev/null
./rtlgen "${ROOT_DIR}/examples/config_mcm_fir.json"
./rtlgen "${ROOT_DIR}/examples/config_cmvm_dct.json"
popd >/dev/null

iverilog -g2012 -o "${BUILD_DIR}/fir3_mcm_tb" \
  "${ROOT_DIR}/tests/fir3_mcm_tb.v" \
  "${BUILD_DIR}/fir3_mcm.v"
vvp "${BUILD_DIR}/fir3_mcm_tb"

iverilog -g2012 -o "${BUILD_DIR}/dct4_cmvm_tb" \
  "${ROOT_DIR}/tests/dct4_cmvm_tb.v" \
  "${BUILD_DIR}/dct4_cmvm.v"
vvp "${BUILD_DIR}/dct4_cmvm_tb"

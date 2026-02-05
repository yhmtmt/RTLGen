#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SCHEDULE="${REPO_ROOT}/npu/mapper/examples/golden_schedule.yml"
DESC_BIN="${REPO_ROOT}/npu/mapper/examples/golden_descriptors.bin"
DESC_YML="${REPO_ROOT}/npu/mapper/examples/golden_descriptors.yml"
RTL_BIN="${REPO_ROOT}/npu/sim/rtl/golden_descriptors.bin"
PERF_TRACE="${REPO_ROOT}/npu/sim/perf/golden_trace.json"
GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_trace.json"

python3 "${REPO_ROOT}/npu/mapper/validate.py" "${SCHEDULE}"
python3 "${REPO_ROOT}/npu/mapper/run.py" "${SCHEDULE}" --out "${DESC_YML}" --out-bin "${DESC_BIN}"
cp "${DESC_BIN}" "${RTL_BIN}"

pushd "${REPO_ROOT}" >/dev/null
make -f npu/sim/rtl/Makefile run BIN="${RTL_BIN}" BYTES=4096 VVPFLAGS="+gemm_mem_test=256"
popd >/dev/null
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${DESC_BIN}" --out "${PERF_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_descriptors.bin" \
  --out "${GEMM_TRACE}" --config "${REPO_ROOT}/npu/sim/perf/example_config.json"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-cycles 1 --clk-ns 10 \
  --perf-trace "${GEMM_TRACE}" --tolerance 0.9

echo "golden flow: ok"

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SCHEDULE="${REPO_ROOT}/npu/mapper/examples/golden_schedule.yml"
DESC_BIN="${REPO_ROOT}/npu/mapper/examples/golden_descriptors.bin"
DESC_YML="${REPO_ROOT}/npu/mapper/examples/golden_descriptors.yml"
RTL_BIN="${REPO_ROOT}/npu/sim/rtl/golden_descriptors.bin"
PERF_TRACE="${REPO_ROOT}/npu/sim/perf/golden_trace.json"
GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_trace.json"
GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_rtl.log"
GEMM2_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_two_trace.json"
GEMM2_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_two_rtl.log"
PERF_CFG="${REPO_ROOT}/npu/sim/perf/example_config.json"
CLK_NS=$(REPO_ROOT="${REPO_ROOT}" python3 - <<'PY'
import json
import os
path = os.path.join(os.environ["REPO_ROOT"], "npu/sim/perf/example_config.json")
with open(path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
print(cfg.get("clk_period_ns", 10.0))
PY
)

python3 "${REPO_ROOT}/npu/mapper/validate.py" "${SCHEDULE}"
python3 "${REPO_ROOT}/npu/mapper/run.py" "${SCHEDULE}" --out "${DESC_YML}" --out-bin "${DESC_BIN}"
cp "${DESC_BIN}" "${RTL_BIN}"

pushd "${REPO_ROOT}" >/dev/null
make -f npu/sim/rtl/Makefile run BIN="${RTL_BIN}" BYTES=4096 VVPFLAGS="+gemm_mem_test=256"
make -f npu/sim/rtl/Makefile run \
  BIN="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_descriptors.bin" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256" | tee "${GEMM_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  BIN="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_two_descriptors.bin" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256" | tee "${GEMM2_RTL_LOG}"
popd >/dev/null
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${DESC_BIN}" --out "${PERF_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_descriptors.bin" \
  --out "${GEMM_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_two_descriptors.bin" \
  --out "${GEMM2_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM2_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM2_TRACE}" --tolerance 0.9

echo "golden flow: ok"

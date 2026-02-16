#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

SCHEDULE="${REPO_ROOT}/npu/mapper/examples/golden_schedule.yml"
DESC_BIN="${REPO_ROOT}/npu/mapper/examples/golden_descriptors.bin"
DESC_YML="${REPO_ROOT}/npu/mapper/examples/golden_descriptors.yml"
GEMM_SCHEDULE="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_schedule.yml"
GEMM_BIN="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_descriptors.bin"
GEMM_YML="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_descriptors.yml"
GEMM2_SCHEDULE="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_two_schedule.yml"
GEMM2_BIN="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_two_descriptors.bin"
GEMM2_YML="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_two_descriptors.yml"
GEMM_OOO_SCHEDULE="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_ooo_schedule.yml"
GEMM_OOO_BIN="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_ooo_descriptors.bin"
GEMM_OOO_YML="${REPO_ROOT}/npu/mapper/examples/golden_gemm_v2_ooo_descriptors.yml"
RTL_BIN="${REPO_ROOT}/npu/sim/rtl/golden_descriptors.bin"
PERF_TRACE="${REPO_ROOT}/npu/sim/perf/golden_trace.json"
GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_trace.json"
GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_rtl.log"
GEMM2_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_two_trace.json"
GEMM2_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_two_rtl.log"
GEMM_OOO_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_ooo_trace.json"
GEMM_OOO_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_ooo_rtl.log"
GEMM_OOO_TOL="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_ooo_tolerance.json"
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
python3 "${REPO_ROOT}/npu/mapper/validate.py" "${GEMM_SCHEDULE}"
python3 "${REPO_ROOT}/npu/mapper/run.py" "${GEMM_SCHEDULE}" --out "${GEMM_YML}" --out-bin "${GEMM_BIN}"
python3 "${REPO_ROOT}/npu/mapper/validate.py" "${GEMM2_SCHEDULE}"
python3 "${REPO_ROOT}/npu/mapper/run.py" "${GEMM2_SCHEDULE}" --out "${GEMM2_YML}" --out-bin "${GEMM2_BIN}"
python3 "${REPO_ROOT}/npu/mapper/validate.py" "${GEMM_OOO_SCHEDULE}"
python3 "${REPO_ROOT}/npu/mapper/run.py" "${GEMM_OOO_SCHEDULE}" --out "${GEMM_OOO_YML}" --out-bin "${GEMM_OOO_BIN}"
cp "${DESC_BIN}" "${RTL_BIN}"

pushd "${REPO_ROOT}" >/dev/null
make -f npu/sim/rtl/Makefile run BIN="${RTL_BIN}" BYTES=4096 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1"
make -f npu/sim/rtl/Makefile run \
  BIN="${GEMM_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${GEMM_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  BIN="${GEMM2_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${GEMM2_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  BIN="${GEMM_OOO_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${GEMM_OOO_RTL_LOG}"
popd >/dev/null
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${DESC_BIN}" --out "${PERF_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_BIN}" \
  --out "${GEMM_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM2_BIN}" \
  --out "${GEMM2_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM2_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM2_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_OOO_BIN}" \
  --out "${GEMM_OOO_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM_OOO_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM_OOO_TRACE}" --tolerance 0.9 \
  --tolerance-map "${GEMM_OOO_TOL}" --require-order-change

echo "golden flow: ok"

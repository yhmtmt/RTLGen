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
MIXED_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_rtl.log"
GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_trace.json"
GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_rtl.log"
GEMM2_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_two_trace.json"
GEMM2_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_two_rtl.log"
GEMM_OOO_TRACE="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_ooo_trace.json"
GEMM_OOO_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_gemm_v2_ooo_rtl.log"
GEMM_OOO_TOL="${REPO_ROOT}/npu/sim/perf/golden_gemm_v2_ooo_tolerance.json"
PERF_CFG="${REPO_ROOT}/npu/sim/perf/example_config.json"
CPP_RTL_CFG="${REPO_ROOT}/npu/rtlgen/examples/minimal_cpp_mac.json"
CPP_PERF_CFG="${REPO_ROOT}/npu/sim/perf/example_config_cpp_mac.json"
CPP_MIXED_TRACE="${REPO_ROOT}/npu/sim/perf/golden_cpp_trace.json"
CPP_MIXED_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_cpp_rtl.log"
CPP_GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_cpp_gemm_v2_trace.json"
CPP_GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_cpp_gemm_v2_rtl.log"
INT16_RTL_CFG="${REPO_ROOT}/npu/rtlgen/examples/minimal_int16.json"
INT16_PERF_CFG="${REPO_ROOT}/npu/sim/perf/example_config_int16.json"
INT16_GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_int16_gemm_v2_trace.json"
INT16_GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_int16_gemm_v2_rtl.log"
FP16_RTL_CFG="${REPO_ROOT}/npu/rtlgen/examples/minimal_fp16.json"
FP16_PERF_CFG="${REPO_ROOT}/npu/sim/perf/example_config_fp16.json"
FP16_GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_fp16_gemm_v2_trace.json"
FP16_GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_fp16_gemm_v2_rtl.log"
FP16_CPP_RTL_CFG="${REPO_ROOT}/npu/rtlgen/examples/minimal_fp16_cpp.json"
FP16_CPP_PERF_CFG="${REPO_ROOT}/npu/sim/perf/example_config_fp16_cpp.json"
FP16_CPP_GEMM_TRACE="${REPO_ROOT}/npu/sim/perf/golden_fp16_cpp_gemm_v2_trace.json"
FP16_CPP_GEMM_RTL_LOG="${REPO_ROOT}/npu/sim/rtl/golden_fp16_cpp_gemm_v2_rtl.log"
CLK_NS=$(REPO_ROOT="${REPO_ROOT}" python3 - <<'PY'
import json
import os
path = os.path.join(os.environ["REPO_ROOT"], "npu/sim/perf/example_config.json")
with open(path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
print(cfg.get("clk_period_ns", 10.0))
PY
)
INT16_CLK_NS=$(REPO_ROOT="${REPO_ROOT}" python3 - <<'PY'
import json
import os
path = os.path.join(os.environ["REPO_ROOT"], "npu/sim/perf/example_config_int16.json")
with open(path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
print(cfg.get("clk_period_ns", 10.0))
PY
)
FP16_CLK_NS=$(REPO_ROOT="${REPO_ROOT}" python3 - <<'PY'
import json
import os
path = os.path.join(os.environ["REPO_ROOT"], "npu/sim/perf/example_config_fp16.json")
with open(path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
print(cfg.get("clk_period_ns", 10.0))
PY
)
FP16_CPP_CLK_NS=$(REPO_ROOT="${REPO_ROOT}" python3 - <<'PY'
import json
import os
path = os.path.join(os.environ["REPO_ROOT"], "npu/sim/perf/example_config_fp16_cpp.json")
with open(path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
print(cfg.get("clk_period_ns", 10.0))
PY
)
CPP_CLK_NS=$(REPO_ROOT="${REPO_ROOT}" python3 - <<'PY'
import json
import os
path = os.path.join(os.environ["REPO_ROOT"], "npu/sim/perf/example_config_cpp_mac.json")
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
make -f npu/sim/rtl/Makefile run \
  BIN="${RTL_BIN}" \
  BYTES=4096 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${MIXED_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  BIN="${GEMM_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${GEMM_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  BIN="${GEMM2_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${GEMM2_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  BIN="${GEMM_OOO_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${GEMM_OOO_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  CONFIG="${CPP_RTL_CFG}" \
  BIN="${RTL_BIN}" \
  BYTES=4096 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${CPP_MIXED_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  CONFIG="${CPP_RTL_CFG}" \
  BIN="${GEMM_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${CPP_GEMM_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  CONFIG="${INT16_RTL_CFG}" \
  BIN="${GEMM_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${INT16_GEMM_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  CONFIG="${FP16_RTL_CFG}" \
  BIN="${GEMM_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1" | tee "${FP16_GEMM_RTL_LOG}"
make -f npu/sim/rtl/Makefile run \
  CONFIG="${FP16_CPP_RTL_CFG}" \
  BIN="${GEMM_BIN}" \
  BYTES=256 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=0" | tee "${FP16_CPP_GEMM_RTL_LOG}"
popd >/dev/null
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${DESC_BIN}" --out "${PERF_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${MIXED_RTL_LOG}" --perf-trace "${PERF_TRACE}"
python3 - "${PERF_TRACE}" <<'PY'
import json
import sys

trace_path = sys.argv[1]
with open(trace_path, "r", encoding="utf-8") as f:
    data = json.load(f)

stats = data.get("stats", {})
vec_ops = int(stats.get("vec_ops", 0))
softmax_ops = int(stats.get("softmax_ops", 0))
unknown_ops = int(stats.get("unknown_ops", 0))
if vec_ops != 3:
    raise SystemExit(f"golden vec regression: expected vec_ops=3, got {vec_ops}")
if softmax_ops != 0:
    raise SystemExit(f"golden vec regression: expected softmax_ops=0, got {softmax_ops}")
if unknown_ops != 0:
    raise SystemExit(f"golden vec regression: expected unknown_ops=0, got {unknown_ops}")

vec_names = [ev.get("op") for ev in data.get("trace", []) if ev.get("name") == "VEC_OP"]
expected = ["add", "mul", "relu"]
if vec_names != expected:
    raise SystemExit(f"golden vec regression: expected vec op order {expected}, got {vec_names}")
print("golden vec regression: OK")
PY
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_BIN}" \
  --out "${GEMM_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${GEMM_RTL_LOG}" --perf-trace "${GEMM_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM2_BIN}" \
  --out "${GEMM2_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM2_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM2_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${GEMM2_RTL_LOG}" --perf-trace "${GEMM2_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_OOO_BIN}" \
  --out "${GEMM_OOO_TRACE}" --config "${PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${GEMM_OOO_RTL_LOG}" --clk-ns "${CLK_NS}" \
  --perf-trace "${GEMM_OOO_TRACE}" --tolerance 0.9 \
  --tolerance-map "${GEMM_OOO_TOL}" --require-order-change
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${GEMM_OOO_RTL_LOG}" --perf-trace "${GEMM_OOO_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${DESC_BIN}" \
  --out "${CPP_MIXED_TRACE}" --config "${CPP_PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${CPP_MIXED_RTL_LOG}" --perf-trace "${CPP_MIXED_TRACE}"
python3 - "${CPP_MIXED_TRACE}" <<'PY'
import json
import sys

trace_path = sys.argv[1]
with open(trace_path, "r", encoding="utf-8") as f:
    data = json.load(f)

stats = data.get("stats", {})
vec_ops = int(stats.get("vec_ops", 0))
softmax_ops = int(stats.get("softmax_ops", 0))
unknown_ops = int(stats.get("unknown_ops", 0))
if vec_ops != 3:
    raise SystemExit(f"golden cpp vec regression: expected vec_ops=3, got {vec_ops}")
if softmax_ops != 0:
    raise SystemExit(f"golden cpp vec regression: expected softmax_ops=0, got {softmax_ops}")
if unknown_ops != 0:
    raise SystemExit(f"golden cpp vec regression: expected unknown_ops=0, got {unknown_ops}")

vec_names = [ev.get("op") for ev in data.get("trace", []) if ev.get("name") == "VEC_OP"]
expected = ["add", "mul", "relu"]
if vec_names != expected:
    raise SystemExit(f"golden cpp vec regression: expected vec op order {expected}, got {vec_names}")
print("golden cpp vec regression: OK")
PY
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_BIN}" \
  --out "${CPP_GEMM_TRACE}" --config "${CPP_PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${CPP_GEMM_RTL_LOG}" --clk-ns "${CPP_CLK_NS}" \
  --perf-trace "${CPP_GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${CPP_GEMM_RTL_LOG}" --perf-trace "${CPP_GEMM_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_BIN}" \
  --out "${INT16_GEMM_TRACE}" --config "${INT16_PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${INT16_GEMM_RTL_LOG}" --clk-ns "${INT16_CLK_NS}" \
  --perf-trace "${INT16_GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${INT16_GEMM_RTL_LOG}" --perf-trace "${INT16_GEMM_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_BIN}" \
  --out "${FP16_GEMM_TRACE}" --config "${FP16_PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${FP16_GEMM_RTL_LOG}" --clk-ns "${FP16_CLK_NS}" \
  --perf-trace "${FP16_GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${FP16_GEMM_RTL_LOG}" --perf-trace "${FP16_GEMM_TRACE}"
python3 "${REPO_ROOT}/npu/sim/perf/run.py" --bin "${GEMM_BIN}" \
  --out "${FP16_CPP_GEMM_TRACE}" --config "${FP16_CPP_PERF_CFG}"
python3 "${REPO_ROOT}/npu/sim/perf/compare_gemm_timing.py" --rtl-log "${FP16_CPP_GEMM_RTL_LOG}" --clk-ns "${FP16_CPP_CLK_NS}" \
  --perf-trace "${FP16_CPP_GEMM_TRACE}" --tolerance 0.9
python3 "${REPO_ROOT}/npu/sim/perf/compare_compute_results.py" \
  --rtl-log "${FP16_CPP_GEMM_RTL_LOG}" --perf-trace "${FP16_CPP_GEMM_TRACE}"

echo "golden flow: ok"

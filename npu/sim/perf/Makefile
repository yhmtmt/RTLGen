PY?=python3
BIN?=npu/mapper/examples/minimal_descriptors.bin
OUT?=/tmp/npu_perf_trace.json
CONFIG?=npu/sim/perf/example_config.json

.PHONY: run

run:
	$(PY) npu/sim/perf/run.py --bin $(BIN) --out $(OUT) --config $(CONFIG) --summary --overlap

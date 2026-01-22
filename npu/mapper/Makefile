PY=python3

EXAMPLE=npu/mapper/examples/minimal_schedule.yml
OUT=npu/mapper/examples/minimal_descriptors.yml
OUT_BIN=npu/mapper/examples/minimal_descriptors.bin

.PHONY: example example-bin validate

example:
	$(PY) npu/mapper/run.py $(EXAMPLE) --out $(OUT)

example-bin:
	$(PY) npu/mapper/run.py $(EXAMPLE) --out-bin $(OUT_BIN)

validate:
	$(PY) npu/mapper/validate.py $(EXAMPLE)

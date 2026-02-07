PY=python3

EXAMPLE=npu/mapper/examples/minimal_schedule.yml
OUT=npu/mapper/examples/minimal_descriptors.yml
OUT_BIN=npu/mapper/examples/minimal_descriptors.bin

MLP1_ONNX=/tmp/mlp1.onnx
MLP1_SCHED=/tmp/mlp1_schedule.yml
MLP1_BIN=/tmp/mlp1_descriptors.bin

MLP2_ONNX=/tmp/mlp2.onnx
MLP2_SCHED=/tmp/mlp2_schedule.yml
MLP2_BIN=/tmp/mlp2_descriptors.bin

.PHONY: example example-bin validate onnx-mlp1 onnx-mlp2

example:
	$(PY) npu/mapper/run.py $(EXAMPLE) --out $(OUT)

example-bin:
	$(PY) npu/mapper/run.py $(EXAMPLE) --out-bin $(OUT_BIN)

validate:
	$(PY) npu/mapper/validate.py $(EXAMPLE)

onnx-mlp1:
	$(PY) npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out $(MLP1_ONNX)
	$(PY) npu/mapper/onnx_to_schedule.py --onnx $(MLP1_ONNX) --arch npu/arch/examples/minimal.yml --out $(MLP1_SCHED)
	$(PY) npu/mapper/run.py $(MLP1_SCHED) --out-bin $(MLP1_BIN)

onnx-mlp2:
	$(PY) npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp2 --out $(MLP2_ONNX)
	$(PY) npu/mapper/onnx_to_schedule.py --onnx $(MLP2_ONNX) --arch npu/arch/examples/minimal.yml --out $(MLP2_SCHED)
	$(PY) npu/mapper/run.py $(MLP2_SCHED) --out-bin $(MLP2_BIN)

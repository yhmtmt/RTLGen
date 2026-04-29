# Mapper (NPU)

## Purpose
This folder contains the schedule IR definition and small examples that map
directly to the shell command descriptors.

## Current status
- v0.1 IR is implemented and can emit YAML or binary descriptors.

Start here:
- `npu/mapper/ir.md` for the v0.1 IR spec.
- `npu/mapper/mapping_contract.md` for the end-to-end mapping contract.
- `npu/mapper/mapping_contract.schema.json` for the contract JSON schema.
- `npu/mapper/examples/minimal_schedule.yml` for a tiny end-to-end example.
- `npu/mapper/examples/golden_schedule.yml` for a tiny golden workload + expected descriptors.
- `npu/mapper/examples/golden_gemm_v2_schedule.yml` for a v0.2 GEMM descriptor example.

Validation:
- `npu/mapper/validate.py` provides a minimal sanity checker for v0.1.

Descriptor emission:
- `npu/mapper/run.py --out <yml>` writes YAML descriptors.
- `npu/mapper/run.py --out-bin <bin>` writes a binary 32B descriptor stream.
  - Used by `npu/sim/rtl/tb_npu_shell.sv` for RTL simulation.

## How to run
```sh
python3 npu/mapper/run.py npu/mapper/examples/minimal_schedule.yml --out-bin /tmp/descriptors.bin
python3 npu/mapper/run.py npu/mapper/examples/golden_schedule.yml --out npu/mapper/examples/golden_descriptors.yml --out-bin npu/mapper/examples/golden_descriptors.bin
```

Golden sim quick check:
```sh
python3 npu/mapper/run.py npu/mapper/examples/golden_schedule.yml --out-bin npu/sim/rtl/golden_descriptors.bin
make -f npu/sim/rtl/Makefile run BIN=npu/sim/rtl/golden_descriptors.bin BYTES=4096
python3 npu/sim/perf/run.py --bin npu/mapper/examples/golden_descriptors.bin --out npu/sim/perf/golden_trace.json
```

GEMM v0.2 descriptor quick check:
```sh
python3 npu/mapper/run.py npu/mapper/examples/golden_gemm_v2_schedule.yml \
  --out-bin npu/mapper/examples/golden_gemm_v2_descriptors.bin
make -f npu/sim/rtl/Makefile run \
  BIN=npu/mapper/examples/golden_gemm_v2_descriptors.bin BYTES=4096
```

## ONNX → schedule IR (MLP v0)
The mapper currently consumes **schedule IR** (`*.yml`). For the RTLGen minimal
NPU demo we start with a small MLP (MatMul/Add/Relu) in ONNX and lower it to
schedule IR.

Tooling:
- `npu/mapper/onnx_to_schedule.py`: ONNX (subset) → schedule IR (`ir.md`)
- `npu/mapper/examples/gen_mlp_onnx_lite.py`: generate tiny MLP ONNX models
  (no external Python deps)
- `npu/mapper/examples/gen_llm_smoke_suite_lite.py`: generate tiny attention-style
  ONNX-lite proxy models with non-terminal `Softmax` for `llm_smoke_v1`.
- `npu/mapper/examples/gen_llm_attention_tail_suite_lite.py`: generate repeated
  attention-tail ONNX-lite proxy models for `llm_attention_tail_v1`.
- `npu/mapper/examples/gen_llm_attention_tail_stress_suite_lite.py`: generate
  the bounded larger-sequence repeated-tail stress set for
  `llm_attention_tail_stress_v1`.

Example (MLP-1):
```sh
python3 npu/mapper/examples/gen_mlp_onnx_lite.py --preset mlp1 --out /tmp/mlp1.onnx
python3 npu/mapper/onnx_to_schedule.py --onnx /tmp/mlp1.onnx --arch npu/arch/examples/minimal.yml --out /tmp/mlp1_schedule.yml
python3 npu/mapper/run.py /tmp/mlp1_schedule.yml --out-bin /tmp/mlp1_descriptors.bin
python3 npu/sim/perf/run.py --bin /tmp/mlp1_descriptors.bin --out /tmp/mlp1_trace.json --config npu/sim/perf/example_config.json --summary --overlap
```

## Next steps
- Extend op coverage and add legality checks against arch configs.
- Add mapper-side split/tiling for oversize ONNX layers so lowering does not
  fail on SRAM-fit limits (phase-1 plan: `npu/docs/mapper_split_plan.md`).

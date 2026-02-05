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

## Next steps
- Extend op coverage and add legality checks against arch configs.

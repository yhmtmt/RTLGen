# Mapper (NPU)

## Purpose
This folder contains the schedule IR definition and small examples that map
directly to the shell command descriptors.

## Current status
- v0.1 IR is implemented and can emit YAML or binary descriptors.

Start here:
- `npu/mapper/ir.md` for the v0.1 IR spec.
- `npu/mapper/examples/minimal_schedule.yml` for a tiny end-to-end example.

Validation:
- `npu/mapper/validate.py` provides a minimal sanity checker for v0.1.

Descriptor emission:
- `npu/mapper/run.py --out <yml>` writes YAML descriptors.
- `npu/mapper/run.py --out-bin <bin>` writes a binary 32B descriptor stream.
  - Used by `npu/sim/rtl/tb_npu_shell.sv` for RTL simulation.

## How to run
```sh
python3 npu/mapper/run.py npu/mapper/examples/minimal_schedule.yml --out-bin /tmp/descriptors.bin
```

## Next steps
- Extend op coverage and add legality checks against arch configs.

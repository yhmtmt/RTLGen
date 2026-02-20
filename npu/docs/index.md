# NPU Documentation Index

## Purpose
This folder contains the living documentation for NPU development in RTLGen.
Documents are grouped by purpose: **specs**, **plans**, and **logs**.

## Current status
- **Implemented**: shell/spec, RTL generator config spec, mapper IR, and RTL/perf simulator docs.
- **Implemented**: OpenROAD block-flow docs and fp16 backend sweep runbooks.
- **Implemented**: fp16 backend `finish`-level comparison report in
  `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`.
- **Implemented**: `arch v0.2-draft` schema + example and `to_rtlgen` v0.2
  derivation path (arch intent -> rtlgen candidate).

## Specs
- `npu/shell/spec.md`: shell contract (MMIO, queue, DMA, events).
- `npu/rtlgen/config_spec.md`: RTLGen NPU config fields.
- `npu/mapper/ir.md`: schedule IR aligned with shell descriptors.
- `npu/sim/report.md`: simulation report schema (draft).
- `npu/docs/arch_v0_2_draft.md`: architecture-layer hierarchy and `arch v0.2` draft direction.

## Plans
- `npu/setup.md`: environment + integration phases.
- `npu/docs/sim_dev_plan.md`: simulator development plan (RTL + performance).
- `npu/synth/plan.md`: OpenROAD integration plan.
- `npu/synth/cacti.md`: CACTI SRAM estimation workflow and scaling rules.
- `npu/docs/workflow.md`: end-to-end workflow guide.

## Runbooks
- `npu/sim/run_golden.sh`: golden regression across RTL + performance simulator.
- `npu/sim/rtl/README.md`: RTL simulation coverage and local commands.
- `npu/sim/perf/README.md`: perf model assumptions, options, and test coverage.
- `npu/synth/run_fp16_backend_sweep.py`: fp16 backend sweep (`builtin_raw16` vs `cpp_ieee`).

## Logs
- `npu/docs/shell_spec_log.md`: shell spec work log.
- `npu/docs/rtl_sim_log.md`: RTL sim bring-up log.

## References
- `npu/docs/nvdla_compatibility.md`: NVDLA compatibility guidance.

## Conventions
- `npu/docs/conventions.md`: documentation structure and status vocabulary.

## Status
- `npu/docs/status.md`: single-page status snapshot.

## Next steps
- Keep `status.md`, `workflow.md`, and synthesis plans synced with each sweep milestone.
- Add explicit runbook for compute-enabled NPU block sweeps beyond fp16 backend comparison.
- Harden `arch v0.2` validation and wire interconnect/mapping constraints into
  mapper/perf policy.

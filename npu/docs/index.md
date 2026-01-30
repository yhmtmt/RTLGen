# NPU Documentation Index

## Purpose
This folder contains the living documentation for NPU development in RTLGen.
Documents are grouped by purpose: **specs**, **plans**, and **logs**.

## Current status
- Specs and RTL simulation docs are implemented.
- SRAM simulation + CACTI PPA documentation are available.
- Performance simulation and OpenROAD flows are planned.

## Specs
- `npu/shell/spec.md`: shell contract (MMIO, queue, DMA, events).
- `npu/rtlgen/config_spec.md`: RTLGen NPU config fields.
- `npu/mapper/ir.md`: schedule IR aligned with shell descriptors.
- `npu/sim/report.md`: simulation report schema (draft).

## Plans
- `npu/setup.md`: environment + integration phases.
- `npu/docs/sim_dev_plan.md`: simulator development plan (RTL + performance).
- `npu/synth/plan.md`: OpenROAD integration plan.
- `npu/synth/cacti.md`: CACTI SRAM estimation workflow and scaling rules.
- `doc/npu_workflow.md`: end-to-end workflow guide.

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
- Fill in performance simulation report schema.
- Add OpenROAD flow details as implementation progresses.

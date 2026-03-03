# NPU Documentation Index

## Purpose
This folder contains the living documentation for NPU development in RTLGen.
Documents are grouped by purpose: **specs**, **plans**, and **logs**.

## Document roles
- `npu/docs/workflow.md`: canonical NPU execution order/runbook.
- `npu/docs/status.md`: concise current snapshot for quick checks.
- `npu/docs/*_plan.md` + `npu/synth/plan.md`: deeper plan detail.
- `npu/docs/*_log.md`: append-only development logs.
- `npu/nvdla/**`: external reference docs (not canonical local policy).

Cross-directory boundaries are defined in `docs/structure.md`.
Two-layer optimization split and interaction contract are defined in
`docs/two_layer_workflow.md`.

## Current status
- **Implemented**: shell/spec, RTL generator config spec, mapper IR, and RTL/perf simulator docs.
- **Implemented**: OpenROAD block-flow docs and fp16 backend sweep runbooks.
- **Implemented**: fp16 backend `finish`-level comparison report in
  `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`.
- **Implemented**: `arch v0.2-draft` schema + example and `to_rtlgen` v0.2
  derivation path (arch intent -> rtlgen candidate).
- **Implemented**: pre-synthesis SRAM stage wrapper with memgen-first policy
  and CACTI fallback.
- **Implemented**: end-to-end evaluation flow contract + campaign tooling
  (`npu/eval/`, `npu/docs/eval_flow_plan.md`,
  `runs/campaigns/npu/e2e_eval_v0/`).

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
- `npu/docs/eval_flow_plan.md`: system-level ONNX + physical + perf flow plan.
- `npu/synth/cacti.md`: CACTI SRAM estimation workflow and scaling rules.
- `npu/docs/workflow.md`: end-to-end workflow guide.

## Runbooks
- `npu/sim/run_golden.sh`: golden regression across RTL + performance simulator.
- `npu/sim/rtl/README.md`: RTL simulation coverage and local commands.
- `npu/sim/perf/README.md`: perf model assumptions, options, and test coverage.
- `npu/synth/pre_synth_memory.py`: pre-synthesis SRAM stage (memgen/cacti policy).
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

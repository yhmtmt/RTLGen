# RTLGen Documentation Index

This directory is the canonical documentation hub for the repository.

Use this index first, then drop into subsystem-local docs only for subsystem
details.

## Top-level map

- `repo/`
  - repository layout
  - environment/bootstrap
- `architecture/`
  - abstraction layers
  - Layer 1 / Layer 2 interaction contract
- `workflows/`
  - Layer 1 workflow
  - developer loop
  - evaluation-lane policy
- `operations/`
  - operator-facing docs and service ownership
- `reference/`
  - stable schemas and artifact contracts
- `backlog/`
  - intake item rules
- `proposals/`
  - proposal workspace rules

## Canonical entry points

- Repository layout:
  - `docs/repo/structure.md`
- Environment/bootstrap:
  - `docs/repo/environment.md`
- Abstraction model:
  - `docs/architecture/layers.md`
- Layer 1 / Layer 2 contract:
  - `docs/architecture/layer_interaction.md`
- Layer 1 runbook:
  - `docs/workflows/layer1.md`
- Developer loop:
  - `docs/workflows/developer_loop.md`
- Internal vs external evaluation lanes:
  - `docs/workflows/evaluation_lanes.md`
- Control-plane operations:
  - `control_plane/operator_runbook.md`
  - `control_plane/daily_operations.md`
- NPU subsystem workflow:
  - `npu/docs/workflow.md`

## Boundary rules

- `docs/` is the cross-repo source of truth for stable shared concepts.
- `control_plane/` holds operator-facing implementation and service runbooks.
- `npu/docs/` holds NPU-specific specs, plans, logs, and runbooks.
- `notes/` holds rationale, studies, and non-canonical working material.
- `plan/` holds chronological execution logs.
- `runs/` holds evaluated evidence and generated artifacts, not policy docs.

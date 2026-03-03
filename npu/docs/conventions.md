# NPU Docs Conventions

This file defines the lightweight conventions for NPU documentation in RTLGen.

## 1) File placement
- **Specs**: `npu/shell/`, `npu/rtlgen/`, `npu/mapper/`, `npu/sim/`
- **Plans/runbooks**: `npu/docs/`, `npu/synth/`
- **Status snapshot**: `npu/docs/status.md`
- **Logs**: `npu/docs/*_log.md`
- **External references**: `npu/nvdla/` (upstream-owned; avoid local policy edits)

Cross-directory role map:
- Repository-wide roles are defined in `docs/structure.md`.
- Two-layer optimization split is defined in `docs/two_layer_workflow.md`.
- `notes/` contains studies/rationale; do not treat it as NPU runbook source of truth.

## 2) Standard section template
For owned docs, prefer the following sections where relevant:
1) **Purpose**
2) **Current status**
3) **Inputs / outputs** (if applicable)
4) **How to run** (if applicable)
5) **Next steps**

## 3) Status vocabulary
Use one of:
- **Implemented**
- **In progress**
- **Planned**
- **Placeholder**

## 4) Cross-links
- Add a link to `npu/docs/index.md` where it helps discovery.
- Cross-link specs to their corresponding testbenches and generators.
- Link to `docs/structure.md` when introducing new doc roots.

## 5) Change discipline
- Keep logs append-only (new entries rather than edits).
- Keep specs stable; use “Open items” for forward changes.

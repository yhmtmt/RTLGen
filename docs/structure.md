# RTLGen Documentation Structure

## Purpose
Define role boundaries for documentation folders so workflow/runbook content,
historical notes, and published artifacts do not drift or duplicate.

## Directory roles
| Path | Role | Canonical content |
|---|---|---|
| `README.md` | Repository entrypoint | High-level project overview and quick links. |
| `development.md` | Environment/bootstrap guide | Toolchain, build environment, and integration notes. |
| `docs/` | Published/static assets | Browser-facing artifacts (`docs/runs/`) and doc navigation aids. |
| `notes/` | Authored studies and guidance | Research notes, comparisons, and contributor guidance. |
| `plan/` | Execution planning log | Rolling plan + append-only activity log (`plan/log.md`). |
| `runs/eval_queue/` | Distributed evaluation queue | GitHub-exchanged OpenROAD task items (`queued/` -> `evaluated/`). |
| `npu/README.md` | NPU subsystem entrypoint | NPU scope, status summary, and top-level pointers. |
| `npu/docs/` | NPU canonical docs hub | NPU workflow, status snapshot, plans, logs, and conventions. |
| `npu/nvdla/` | Vendor/reference mirror | Upstream NVDLA docs and references (external ownership). |

## Canonical precedence
When content overlaps, use this precedence:
1. Layer 1 runbook: `docs/layer1_circuit_workflow.md`
2. Layer 2 runbook: `npu/docs/workflow.md`
3. NPU current snapshot: `npu/docs/status.md`
4. NPU plan detail: `npu/docs/*_plan.md` + `npu/synth/plan.md`
5. Cross-domain notes and rationale: `notes/*.md`
6. Historical execution trail: `plan/log.md`

## Optimization layers
- Layer model and interaction contract: `docs/two_layer_workflow.md`
- Layer 1 runbook: `docs/layer1_circuit_workflow.md`
- Layer 1 (circuit module physical loop): module generation + OpenROAD PPA
- Layer 2 (NPU architecture model loop): ONNX/perf/campaign optimization with
  Layer 1 module candidates

## Consistency rules
- Keep one canonical home per topic; cross-link instead of duplicating text.
- Use `notes/` for rationale/studies, not operational source-of-truth runbooks.
- Keep `plan/log.md` append-only; avoid rewriting prior observations.
- Treat `npu/nvdla/` documents as external references unless explicitly adopting
  local policy in `npu/docs/`.

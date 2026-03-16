# RTLGen Documentation Structure

## Purpose
Define role boundaries for documentation folders so workflow/runbook content,
historical notes, and published artifacts do not drift or duplicate.

## Directory roles
| Path | Role | Canonical content |
|---|---|---|
| `README.md` | Repository entrypoint | High-level project overview and quick links. |
| `docs/` | Canonical shared documentation | Stable policy, workflow contracts, runbooks, and documentation navigation. |
| `docs/development.md` | Environment/bootstrap guide | Toolchain, build environment, and integration notes. |
| `control_plane/` | Internal evaluation operations | DB-backed scheduling, worker/completion operation, and control-plane runbooks. |
| `notes/` | Working notes and rationale | Research notes, comparisons, exploratory guidance, and non-canonical rationale. |
| `plan/` | Execution planning log | Rolling plan + append-only activity log (`plan/log.md`). |
| `runs/eval_queue/` | Distributed evaluation queue | GitHub-exchanged OpenROAD task items (`queued/` -> `evaluated/`). |
| `npu/README.md` | NPU subsystem entrypoint | NPU scope, status summary, and top-level pointers. |
| `npu/docs/` | NPU canonical docs hub | NPU workflow, status snapshot, plans, logs, and conventions. |
| `npu/nvdla/` | Vendor/reference mirror | Upstream NVDLA docs and references (external ownership). |

## Canonical precedence
When content overlaps, use this precedence:
1. Internal evaluation operations: `control_plane/operator_runbook.md`
2. Evaluation-lane policy: `docs/internal_external_evaluator_policy.md`
3. Notebook developer-agent loop: `docs/developer_agent_loop.md`
4. Developer-agent first-read policy: `docs/developer_agent_first_read.md`
5. Developer-agent review contract: `docs/developer_agent_review.md`
6. Developer-agent artifact schemas: `docs/developer_agent_artifacts.md`
7. Developer-agent orchestration procedure: `docs/developer_agent_orchestration.md`
8. Layer 1 runbook: `docs/layer1_circuit_workflow.md`
9. Layer 2 runbook: `npu/docs/workflow.md`
10. NPU current snapshot: `npu/docs/status.md`
11. NPU plan detail: `npu/docs/*_plan.md` + `npu/synth/plan.md`
12. Cross-domain notes and rationale: `notes/*.md`
13. Historical execution trail: `plan/log.md`

## Optimization layers
- Layer model and interaction contract: `docs/two_layer_workflow.md`
- Internal vs external evaluation policy: `docs/internal_external_evaluator_policy.md`
- Notebook-side autonomous development loop: `docs/developer_agent_loop.md`
- Layer 1 runbook: `docs/layer1_circuit_workflow.md`
- Layer 1 (circuit module physical loop): module generation + OpenROAD PPA
- Layer 2 (NPU architecture model loop): ONNX/perf/campaign optimization with
  Layer 1 module candidates

## Consistency rules
- Keep one canonical home per topic; cross-link instead of duplicating text.
- Use `docs/` for stable source-of-truth material:
  - policy
  - workflow contracts
  - runbooks
  - shared terminology and rules
- Use `notes/` for non-canonical material:
  - rationale
  - design studies
  - comparisons
  - exploratory guidance
  - transitional contributor notes
- If a note becomes stable operational policy, move it into `docs/` or another canonical home.
- Keep `plan/log.md` append-only; avoid rewriting prior observations.
- Treat `npu/nvdla/` documents as external references unless explicitly adopting
  local policy in `npu/docs/`.

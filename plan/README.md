# Planning Workspace

## Purpose
`plan/` is the lightweight planning workspace for active execution tracking.

## Role
- Keep rolling milestones and short-horizon plan context.
- Keep the forward-looking repository roadmap in `plan/roadmap.md`.
- Keep an append-only execution/activity trail in `plan/log.md`.
- Link out to canonical runbooks and status pages rather than duplicating them.

## Canonical companions
- Repository doc role map: `docs/structure.md`
- NPU workflow/runbook: `npu/docs/workflow.md`
- NPU status snapshot: `npu/docs/status.md`
- NPU detailed plans: `npu/docs/*_plan.md`, `npu/synth/plan.md`
- Notes/studies: `notes/index.md`

## Usage rules
- Keep the long-range roadmap in `plan/roadmap.md`.
- Add new execution observations to `plan/log.md` in chronological order.
- Prefer links to result artifacts (`runs/`, reports, scripts) over long copies.
- If a plan graduates into a stable runbook, move it to the appropriate
  canonical location and keep only a pointer here.

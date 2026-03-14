# docs/ (Canonical Shared Docs)

This directory contains canonical shared documentation for the repo:
- stable policies
- workflow contracts
- runbooks
- doc navigation helpers
- browser-facing static assets

## Contents
- `docs/runs/`: static evaluation browser and assets.
- `docs/structure.md`: repository documentation role map and precedence rules.
- `docs/layer1_circuit_workflow.md`: canonical Layer 1 module optimization runbook.
- `docs/two_layer_workflow.md`: circuit-layer vs NPU-layer workflow split and
  handoff contract.
- `docs/internal_external_evaluator_policy.md`: evaluation-lane policy.
- `docs/runs_artifact_policy.md`: shared artifact rules across evaluation lanes.

## Boundaries
- Working notes, studies, and exploratory contributor guidance belong in `notes/`.
- Planning and chronological execution logs belong in `plan/`.
- Canonical NPU workflow/status/plan docs belong in `npu/docs/`.
- Control-plane operator procedures belong in `control_plane/`.

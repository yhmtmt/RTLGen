Runs Layer-Bridge Candidates
============================

Purpose
-------
This directory stores machine-readable Layer 1 module candidates that are
eligible for Layer 2 (NPU architecture) consumption.

Layout
------
- `runs/candidates/module_candidates.schema.json`:
  schema for candidate manifests.
- `runs/candidates/<pdk>/module_candidates.json`:
  per-PDK candidate sets with traceable references to Layer 1 physical metrics.

Required traceability
---------------------
Each candidate must include:
- `variant_id`
- `module`
- `evaluation_scope`:
  - `wrapped_io`: evaluated as wrapper-level block with IO registers
  - `macro_hardened`: evaluated as hardened macro view
- `config_hash`
- `metrics_ref` pointing to a concrete `runs/designs/.../metrics.csv` row

Optional handoff fields
-----------------------
- `macro_manifest` when a hardened macro view is available and intended for
  hierarchical top-level use.

Layer 2 guardrail
-----------------
- Campaigns that consume `wrapped_io` candidates must set
  `layer1_modules.allow_wrapped_io=true` explicitly in the architecture point.
- Otherwise, campaign validation fails and asks for `macro_hardened` candidates.

Notes
-----
- Candidate manifests are append/extend oriented; avoid rewriting historical
  IDs unless the referenced artifact is invalid.
- Validation is done by `scripts/validate_runs.py`.

# Repository Structure

## Purpose

Define the primary role of each top-level subtree and reduce documentation
drift between repo entrypoints.

## Top-level directories

| Path | Role | Notes |
|---|---|---|
| `README.md` | Repository entrypoint | Short project overview and links into `docs/`. |
| `docs/` | Canonical shared documentation | Stable policies, workflow contracts, and navigation. |
| `src/` | Core C++ RTL generator sources | Layer 1 circuit-generation implementation. |
| `apps/` | CLI entrypoints | `rtlgen` and related frontends. |
| `npu/` | NPU subsystem source tree | Architecture generation, mapper, simulation, synthesis, eval. |
| `control_plane/` | Evaluation orchestration implementation | DB-backed scheduling, worker, completion, API, operator scripts. |
| `examples/` | Example configs | Small reproducible entry configs. |
| `tests/` | Regression tests | Unit, smoke, and flow regressions. |
| `scripts/` | Shared project scripts | Build, generation, indexing, migration helpers. |
| `runs/` | Generated and committed evaluation evidence | Designs, campaigns, summaries, indexes. |
| `notes/` | Working notes and studies | Non-canonical rationale and exploratory writing. |
| `plan/` | Planning and chronological log | Append-only planning/execution records. |
| `analysis/` | Historical analysis outputs | Heavy analysis material, not core source docs. |
| `materials/` | Static images and presentation assets | Screenshots and sample visual assets. |
| `third_party/` | Bundled third-party source/material | Only repo-coupled dependencies that must live in-tree. |
| `build/` | Local build outputs | Local/generated, not conceptual documentation. |

## Documentation ownership

- Cross-repo policy and workflow:
  - `docs/`
- Control-plane operations:
  - `control_plane/operator_runbook.md`
  - `control_plane/daily_operations.md`
- NPU subsystem docs:
  - `npu/docs/`
- Non-canonical notes:
  - `notes/`

## Separation rule

Keep these concerns separate:

- source:
  - `src/`, `apps/`, `npu/`, `control_plane/`
- canonical docs:
  - `docs/`, subsystem-local runbooks/specs
- generated evidence:
  - `runs/`
- historical notes and logs:
  - `notes/`, `plan/`, `analysis/`

Do not use generated evidence directories as documentation hubs, and do not
use notes/log directories as canonical policy.

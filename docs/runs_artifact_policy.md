# Runs Artifact Policy

Purpose:
- define which generated artifacts under `runs/` belong in Git,
- keep the repository reviewable and reproducible,
- prevent large or transient execution products from accumulating as untracked noise.

## Principle

Track the minimal evidence needed to:
- reproduce the meaning of a result,
- review a decision in a PR,
- trace provenance from inputs to selected outputs.

Do not track the full execution footprint.

A generated file under `runs/` should be tracked only if it is:
- small enough to review in Git,
- stable enough to be compared across commits,
- directly used for ranking, promotion, or audit,
- awkward to reconstruct mentally from other tracked files.

A generated file under `runs/` should not be tracked if it is:
- bulky,
- machine-local,
- transient scratch data,
- an execution cache,
- a detailed implementation byproduct whose existence can be referenced indirectly.

## Tracked Artifacts

These are the normal Git-tracked evidence classes under `runs/`.

Queue and decision state:
- `runs/eval_queue/**/*.json`
- `runs/candidates/**/*.json`
- `runs/index.csv`

Model-set manifests and metadata:
- `runs/models/**/manifest.json`
- `runs/models/**/README.md`

Campaign definitions and reviewable summaries:
- `runs/campaigns/**/campaign.json`
- `runs/campaigns/**/report.md`
- `runs/campaigns/**/results.csv`
- `runs/campaigns/**/summary.csv`
- `runs/campaigns/**/pareto.csv`
- `runs/campaigns/**/best_point.json`
- `runs/campaigns/**/objective_sweep.csv`
- `runs/campaigns/**/objective_sweep.md`
- `runs/campaigns/**/objective_profiles/**/*.md`
- `runs/campaigns/**/objective_profiles/**/*.csv`
- `runs/campaigns/**/objective_profiles/**/*.json`

Design-level lightweight summaries:
- `runs/designs/**/metrics.csv`
- `runs/designs/**/macro_manifest.json`

The rule behind this set:
- if a file is the concise summary humans will review, track it.

## Untracked Artifacts

These are execution products that should normally stay out of Git.

Scratch and intermediate directories:
- `runs/**/artifacts/`
- `runs/**/work/`
- `runs/**/comparisons/`

Large physical-design binaries and layouts:
- `runs/**/*.gds`
- `runs/**/*.def`

Fetched external inputs and caches:
- `runs/model_cache/**`

The rule behind this set:
- if a file is primarily for local execution, debug, or bulk storage, do not track it.

## Portable Paths vs Tracked Files

Some tracked files refer to untracked artifacts, for example:
- `result_path`
- `work_result_json`

Requirement:
- these references must be repo-portable paths, not machine-local absolute paths.

Non-requirement:
- the referenced target does not need to be tracked in Git if it belongs to an untracked artifact class such as `work/`.

This distinction is intentional:
- provenance paths must be stable,
- bulky implementation outputs do not need to live in the repository.

## Shadow Runs

Control-plane shadow runs should not write evaluated snapshots into the live queue tree by default.

Default shadow export location:
- `control_plane/shadow_exports/`

Reason:
- avoids duplicate queue ids against `runs/eval_queue/openroad/queued/`
- keeps local validation outputs separate from reviewable repo evidence

Only promote a shadow-run output into the live `runs/eval_queue/` tree when it is intentionally being turned into tracked evidence.

## Remote Transport

Remote evaluator transport is intentionally narrower than local generation.

Workers may inline and ship only lightweight canonical evidence files such as:
- `runs/index.csv`
- `runs/designs/**/metrics.csv`
- `runs/designs/**/macro_manifest.json`
- `runs/campaigns/**/campaign.json`
- `runs/campaigns/**/report.md`
- `runs/campaigns/**/results.csv`
- `runs/campaigns/**/summary.csv`
- `runs/campaigns/**/pareto.csv`
- `runs/campaigns/**/best_point.json`
- `runs/campaigns/**/objective_sweep.csv`
- `runs/campaigns/**/objective_sweep.md`

Workers should not transport:
- `runs/**/work/`
- `runs/**/artifacts/`
- `runs/**/comparisons/`
- `runs/model_cache/**`
- `control_plane/shadow_exports/**`

Notebook-side completion should materialize only that same allowlisted set.

## Operational Retention Defaults

Recommended starting windows for control-plane cleanup:
- runtime pid/log files under `/tmp/rtlgen-control-plane`: 3 days
- worker logs under `control_plane/logs/`: 14 days
- released/expired DB leases and transient DB artifacts: 30 days

Reasoning:
- runtime files are purely local process state
- worker logs are useful for short-horizon triage
- DB transient rows are useful for audit and debugging longer than local logs

## PR Guidance

Normal PRs should include:
- queue items,
- campaign summaries,
- candidate manifests,
- lightweight design metrics,
- docs explaining decisions.

Normal PRs should exclude:
- `work/`
- `artifacts/`
- `comparisons/`
- local caches
- local control-plane shadow exports

## Enforcement Direction

The expected enforcement order is:
1. document the policy,
2. ignore the clearly transient directories,
3. keep validator checks focused on accidental commits of bulky run artifacts.

This policy is intentionally narrow:
- summaries stay visible,
- scratch output stays local.

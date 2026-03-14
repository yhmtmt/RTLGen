# Runs Artifact Policy

Purpose:
- define which generated artifacts under `runs/` belong in Git,
- keep the repository reviewable and reproducible,
- prevent large or transient execution products from accumulating as untracked noise.
- describe both evaluation lanes:
  - internal control-plane execution
  - external/manual queue-and-PR execution

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

## Lane Split

RTLGen now has two evaluation lanes:

1. Internal/trusted lane
- DB-backed control plane
- remote workers execute and ship only allowlisted lightweight evidence
- notebook completion consumes and may auto-submit the review PR

2. External/manual lane
- queue JSON plus GitHub PR workflow
- evaluator runs the task manually
- evaluator commits lightweight evidence directly in the PR branch

The tracked evidence classes below apply to both lanes.
What differs is how those files move from execution environment to Git.

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

## Internal Control-Plane Lane

Internal workers may generate large local execution state, but only a narrower
reviewable subset should be transported and rematerialized on the notebook.

This lane uses:
- `control_plane/operator_runbook.md`
- `control_plane/remote_operator_workflow.md`

### Remote Transport

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

This rule exists because internal workers execute out of disposable worktrees
and should not copy bulky or machine-local byproducts back into the notebook
checkout.

## External Manual Queue/PR Lane

The external/manual lane does not use DB artifact transport.
The evaluator commits lightweight evidence directly into the PR branch.

This lane uses:
- `runs/eval_queue/README.md`
- `notes/evaluation_agent_guidance.md`

For this lane:
- commit only lightweight, reviewable artifacts
- keep `result_path` and related provenance fields repo-portable
- do not commit machine-local paths, scratch directories, or bulky flow outputs
- ensure evaluated queue items reference real tracked metrics rows
- include the exact queue/result provenance fields required by the queue rules

In other words:
- internal lane constrains what can be transported automatically
- external lane constrains what can be committed manually
- both lanes converge on the same Git-tracked evidence classes

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

Normal PRs in either lane should include:
- queue items,
- campaign summaries,
- candidate manifests,
- lightweight design metrics,
- docs explaining decisions.

Normal PRs in either lane should exclude:
- `work/`
- `artifacts/`
- `comparisons/`
- local caches
- local control-plane shadow exports

Lane-specific emphasis:
- internal lane:
  - PR is the publication boundary after control-plane execution
  - transported evidence must stay inside the allowlist above
- external/manual lane:
  - PR is both submission boundary and review boundary
  - evaluator must curate the committed files directly

## Enforcement Direction

The expected enforcement order is:
1. document the policy,
2. ignore the clearly transient directories,
3. keep validator checks focused on accidental commits of bulky run artifacts.

This policy is intentionally narrow:
- summaries stay visible,
- scratch output stays local.

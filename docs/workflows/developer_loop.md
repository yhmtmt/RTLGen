# Developer Loop

## Purpose

Define the notebook-side proposal loop that sits above deterministic evaluator
execution.

## Role split

Notebook / developer side:

- proposes directions
- edits code and configs
- requests evaluation
- analyzes results
- prepares decisions

Evaluator side:

- runs deterministic worker/completion/submission services
- executes queued tasks
- does not invent new proposals or policies

## Lifecycle

1. capture an idea in the backlog
2. promote it to a proposal workspace
3. implement and smoke-test
4. pass quality/evaluation gates
5. queue deterministic remote evaluation
6. review and merge evidence PRs
7. finalize proposal decision

## Canonical storage split

Canonical navigation and new-work creation now use:

Intake/backlog:

- `docs/backlog/`

Proposal workspaces:

- `docs/proposals/`

Legacy storage still exists during migration:

- canonical backlog index: `docs/backlog/`
- canonical proposal workspaces: `docs/proposals/`

Use the canonical trees for new work. Drop to the legacy trees only when a
historical item or proposal has not yet been physically moved.

## Service ownership rule

The evaluator container is the sole node allowed to run:

- worker daemon
- completion loop
- GitHub poller
- auto-finalizer
- submission path

Developer/notebook containers must not run competing background services.

## Proposal artifact contract

Current core proposal files:

- `proposal.json`
- `design_brief.md`
- `implementation_summary.md`
- `evaluation_gate.md`
- `evaluation_requests.json`
- `quality_gate.md`
- `analysis_report.md`
- `promotion_decision.json`
- `promotion_result.json`

These files are repeated across proposals by design, but their schema should be
kept tight and consistent.

## Evaluation proposal linkage contract

Every developer-loop work item that may enter `artifact_sync` must carry
`developer_loop.proposal_id` and `developer_loop.proposal_path` in its queued
payload. `proposal_path` is a repo-relative pointer to the proposal's
`proposal.json`; use `docs/proposals/<proposal_id>/proposal.json` when writing
payloads directly. Do not queue a broad ancestor such as `docs/proposals/`.

Before dispatch, the proposal workspace must contain at least:

- `proposal.json`
- `evaluation_requests.json`

`evaluation_requests.json` should name the item ids being queued. When evidence
is exported, the artifact PR must be self-contained: the PR body's
`reviewer_first_read` paths must exist in that PR branch, including the
proposal scaffold. The submission path resolves `proposal_path` to a single
`proposal.json` and packages files from that proposal directory.

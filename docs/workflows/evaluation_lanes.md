# Evaluation Lanes

## Purpose

Define the project policy for trusted internal evaluation versus external PR
driven evaluation.

## Internal lane

Use the DB-backed control plane for trusted machines.

Characteristics:

- scheduler/lease based
- deterministic worker execution
- evaluation runs do not require a PR one by one
- reviewed PRs remain the evidence boundary

## External lane

Use GitHub-mediated task execution and PR submission.

Characteristics:

- no DB credentials
- no scheduler write access
- bounded task definition
- review through PRs only

## Shared contract

Both lanes must preserve:

- lightweight committed evidence
- explicit task identity
- reproducible metrics linkage
- validator-clean metadata

## Internal service ownership

For the trusted internal lane:

- the evaluator container is the single live execution/submission node
- developer containers may inspect, edit, queue, and review
- developer containers must not run competing worker/completion/finalization
  services

## Canonical operator docs

- `control_plane/operator_runbook.md`
- `control_plane/daily_operations.md`

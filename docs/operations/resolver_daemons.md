# Resolver Daemons

This document covers the cross-environment resolver daemons that run beside the
control plane.

Use it for:
- what the resolver currently detects and fixes
- what the A-D validation tests proved
- what the resolver still does not do automatically
- how to rerun the resolver validation tests

## Scope

The resolver subsystem has two long-running processes:

- dev resolver
  - runs on the notebook/server side
  - detects stale `RUNNING` items and blocked `ARTIFACT_SYNC` items
  - opens or updates GitHub issues
  - applies the currently allowed safe remediations
- eval resolver
  - runs on the evaluator side
  - syncs resolver issue state and diagnosis context from GitHub
  - does not own control-plane code changes

The DB remains the source of truth for:
- work item state
- leases
- runs
- resolver cases
- resolver actions

GitHub issues are only the cross-environment mailbox and audit trail.

## What The Resolver Does Today

Implemented detection:
- orphaned running items
  - `RUNNING` item
  - expired active lease
  - nonterminal latest event
  - grace window before issue creation
- blocked submission items
  - `ARTIFACT_SYNC` item
  - concrete submission or eligibility failure evidence

Implemented safe automated actions:
- `expire_stale_lease`
  - diagnosis-driven
- `retry_submission`
  - diagnosis-driven

Implemented safety controls:
- per-case attempt budgets
- same-evidence anti-loop guard
- duplicate suppression for unchanged evidence
- case scoping by item episode, not only fingerprint
- stale-case cleanup for superseded or merged items

## What A-D Proved

Test A: orphaned running path
- long DB/network outage can produce a real stale-lease orphaned run
- short false positives were reduced by the orphaned grace window
- the dev resolver now survives DB loss and GitHub API failures during outages
- closed orphaned issues are not reused for new episodes

Test B: blocked submission retry
- `gh pr create failed` is detected as a blocked-submission case
- evaluator diagnosis can recommend `retry_submission`
- the dev resolver can queue the retry automatically
- submission retry can open the PR without rerunning evaluation

Test C: anti-loop escalation
- when the same remediation is retried against unchanged evidence, the resolver
  stops and escalates
- it does not keep queueing the same retry indefinitely

Test D: duplicate suppression
- repeated unchanged resolver polls keep one active case and one issue
- unchanged evidence does not create duplicate `open_issue`
- duplicate `evidence_changed` comment churn is suppressed

## Known Limits

The resolver still does not do everything automatically.

Current limits:
- the evaluator resolver is still mainly a diagnosis/sync component, not a
  broad autonomous repair agent
- the worker can survive DB loss at the daemon level, but long DB outages can
  still interrupt in-flight run semantics
- submission recovery history is summarized in review artifacts, but PR review
  still remains a human decision
- the resolver should not be treated as a replacement for normal operator
  monitoring

Practical rule:
- leave the resolver running in the background
- do not build new work around forcing resolver incidents unless validating a
  specific new fix

## Service Control

Dev resolver:
```sh
/workspaces/RTLGen/.devcontainer/control_plane_service_ctl.sh restart resolver
```

Evaluator resolver:
```sh
sudo systemctl restart rtlgen-evaluator-resolver.service
```

One-shot dev poll:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane python3 -m control_plane.cli.main run-dev-resolver   --database-url "$RTLCP_DATABASE_URL"   --repo yhmtmt/RTLGen   --repo-root /workspaces/RTLGen
```

One-shot eval poll:
```sh
source /workspaces/RTLGen/control_plane/.venv/bin/activate
PYTHONPATH=/workspaces/RTLGen/control_plane python3 -m control_plane.cli.main run-eval-resolver   --database-url "$RTLCP_DATABASE_URL"   --repo yhmtmt/RTLGen   --machine-key "$RTLCP_MACHINE_KEY"
```

## How To Rerun The Validation Tests

Use cheap proposal-backed Layer 1 items only.

Test A: orphaned running
1. Run a cheap item on the remote evaluator.
2. Wait until `run_sweep` starts.
3. Remove DB/network connectivity from the notebook side long enough to exceed
   the lease window and the orphaned grace window.
4. Reconnect and inspect:
   - work item state
   - resolver case
   - resolver actions
   - GitHub issue creation behavior

Test B: retry submission
1. Run a cheap proposal-backed item that reliably reaches submission.
2. Log out `gh` on the evaluator before submission.
3. Let the item fail in `ARTIFACT_SYNC` with `gh pr create failed`.
4. Restore `gh`.
5. Post a diagnosis recommending `retry_submission`.
6. Verify the resolver queues a submission retry and the PR opens without
   rerunning evaluation.

Test C: anti-loop
1. Recreate the Test B failure.
2. Keep the failure condition unchanged across the automatic retry.
3. Verify the resolver escalates instead of retrying forever.

Test D: duplicate suppression
1. Recreate one stable blocked-submission case.
2. Do not change evidence and do not post diagnosis.
3. Run repeated resolver polls.
4. Verify there is still:
   - one active case
   - one issue
   - one `open_issue`
   - no repeated unchanged-evidence comments

## What To Watch In Production

After deployment, the useful production checks are:
- orphaned-running issues open only for real long-lived stale cases
- blocked-submission issues match the actual run/submission evidence
- retries are attempted once per evidence state
- stale superseded test items do not keep issues open

If production remains quiet, do not keep changing the resolver.

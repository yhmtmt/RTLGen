Evaluation Queue
================

Purpose
-------
- Track heavyweight evaluation work items (especially OpenROAD) in a
  GitHub-exchangeable queue.
- Let lightweight/dev environments author tasks while high-performance
  evaluators execute them.
- Serve as the external/manual evaluation lane.

For the internal trusted-machine lane, use the DB-backed control plane instead:
- `control_plane/operator_runbook.md`
- `docs/internal_external_evaluator_policy.md`

Evaluator first-read
--------------------
- `notes/evaluation_agent_guidance.md` is the evaluator's first-read manual
  before executing queue items.
- Maintainer PR triage uses `notes/evaluation_pr_triage.md`.

Layout
------
- `runs/eval_queue/openroad/item.schema.json`:
  schema for OpenROAD evaluation items.
- `runs/eval_queue/openroad/templates/item_template.json`:
  template for new items.
- `runs/eval_queue/openroad/queued/*.json`:
  requested, not-yet-completed evaluation items.
- `runs/eval_queue/openroad/evaluated/*.json`:
  completed items with result payload and metrics references.

Workflow
--------
1. Requester adds a `queued` item JSON and pushes to GitHub.
2. Evaluator creates a branch `eval/<item_id>/<session_id>` on high-performance machine.
3. Evaluator runs commands, commits lightweight artifacts/results, and updates
   the item JSON with execution result.
4. Evaluator moves item file from `queued/` to `evaluated/` in the same PR.
5. PR must pass `scripts/validate_runs.py` and include traceable metrics rows.

This queue/PR workflow is still valid, but it is no longer the primary
internal production execution path.
Internal routine evaluation now runs through the control plane and publishes
reviewed result batches back to Git only when warranted.

Rules
-----
- Keep one item per file.
- `item_id` must be globally unique across queued+evaluated.
- `state` must match parent directory (`queued` or `evaluated`).
- `task.source_mode` is required:
  - `config`: harden raw RTLGen modules via `--config`.
  - `src_verilog`: harden existing generated RTL/wrapper modules via
    `--src_verilog_dir`.
- Wrapper modules (`*_wrapper`) must use `source_mode=src_verilog`.
- Use branch format `eval/<item_id>/<session_id>` for evaluator runs.
- PR body must include: `evaluator_id`, `session_id`, `host`, `queue_item_id`.
- PR conversation comments should start with identity block:
  `[role:evaluator][account:<evaluator_id>][session:<session_id>][host:<host>][item:<queue_item_id>]`.
- Evaluated items with `result.status=ok` must reference at least one real
  `metrics.csv` row.
- Evaluated item `result` must carry the same identity/provenance fields as PR
  body and include canonical `identity_block`.
- Before moving an item to `evaluated/`, replace placeholder values in
  `handoff.pr_body_fields` with the concrete evaluator/session/host values.
- New committed `result_path` values in `metrics.csv`, `runs/index.csv`, and
  evaluated queue `metrics_rows` must reference the repo-tracked artifact path
  under `runs/designs/.../work/<hash>/result.json`, not evaluator-local
  checkout paths such as `/tmp/...`.
- Do not add large binaries (DEF/GDS/log dumps) to the queue directories.

Validation
----------
```sh
python3 scripts/validate_runs.py
```

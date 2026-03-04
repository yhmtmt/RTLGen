Evaluation Queue
================

Purpose
-------
- Track heavyweight evaluation work items (especially OpenROAD) in a
  GitHub-exchangeable queue.
- Let lightweight/dev environments author tasks while high-performance
  evaluators execute them.

Evaluator first-read
--------------------
- `notes/evaluation_agent_guidance.md` is the evaluator's first-read manual
  before executing queue items.

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
2. Evaluator creates a branch `eval/<item_id>` on high-performance machine.
3. Evaluator runs commands, commits lightweight artifacts/results, and updates
   the item JSON with execution result.
4. Evaluator moves item file from `queued/` to `evaluated/` in the same PR.
5. PR must pass `scripts/validate_runs.py` and include traceable metrics rows.

Rules
-----
- Keep one item per file.
- `item_id` must be globally unique across queued+evaluated.
- `state` must match parent directory (`queued` or `evaluated`).
- Evaluated items with `result.status=ok` must reference at least one real
  `metrics.csv` row.
- Do not add large binaries (DEF/GDS/log dumps) to the queue directories.

Validation
----------
```sh
python3 scripts/validate_runs.py
```

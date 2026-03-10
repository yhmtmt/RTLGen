# DB-native Generator/Consumer Shadow Run

Purpose:
- validate the control-plane workflow without queue import,
- prove that generator-created work items can be executed by the internal worker,
- prove that the matching consumers can emit reviewable proposals from completed runs.

Date:
- 2026-03-10 UTC

Execution mode:
- temporary lightweight repo under `/tmp`
- temporary SQLite database
- real control-plane generator, worker, and consumer code from `master`
- stubbed workload scripts inside the temp repo to validate orchestration rather than spend OpenROAD runtime

Temp execution roots:
- repo:
  - `/tmp/rtlcp_agent_cycle_sSBXu7/repo`
- db:
  - `/tmp/rtlcp_agent_cycle_sSBXu7/cp.db`
- terminal log:
  - `/tmp/rtlcp_agent_cycle_sSBXu7/agent_cycle.log`

## Layer 1 Cycle

Generated work item:
- `l1_demo_db_native`

Generator command:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l1-sweep \
  --database-url sqlite+pysqlite:////tmp/rtlcp_agent_cycle_sSBXu7/cp.db \
  --repo-root /tmp/rtlcp_agent_cycle_sSBXu7/repo \
  --sweep-path runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json \
  --configs examples/config_softmax_rowwise_int8.json examples/config_softmax_rowwise_int8_r8_acc20.json \
  --platform nangate45 \
  --out-root runs/designs/activations \
  --requested-by @codex \
  --item-id l1_demo_db_native \
  --source-commit demohead
```

Worker outcome:
- `run_key`:
  - `l1_demo_db_native_run_4c48ad35599d2994`
- status:
  - `SUCCEEDED`
- summary:
  - `4/4 commands succeeded`

Consumer outcome:
- proposal path:
  - `control_plane/shadow_exports/l1_promotions/l1_demo_db_native.json`
- proposal count:
  - `2`
- final work item state:
  - `AWAITING_REVIEW`

## Layer 2 Cycle

Generated work item:
- `l2_demo_db_native`

Generator command:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l2-campaign \
  --database-url sqlite+pysqlite:////tmp/rtlcp_agent_cycle_sSBXu7/cp.db \
  --repo-root /tmp/rtlcp_agent_cycle_sSBXu7/repo \
  --campaign-path runs/campaigns/npu/demo_campaign/campaign.json \
  --objective-profiles-json runs/campaigns/npu/base/objective_profiles.json \
  --requested-by @codex \
  --item-id l2_demo_db_native \
  --source-commit demohead
```

Worker outcome:
- `run_key`:
  - `l2_demo_db_native_run_2672cbfea5a59063`
- status:
  - `SUCCEEDED`
- summary:
  - `5/5 commands succeeded`

Consumer outcome:
- decision path:
  - `control_plane/shadow_exports/l2_decisions/l2_demo_db_native.json`
- recommended point:
  - `arch_id=fp16_nm1_demo`
  - `macro_mode=flat_nomacro`
- objective profile count:
  - `2`
- final work item state:
  - `AWAITING_REVIEW`

## Observed Run Events

Layer 1:
- `run_started`
- `checkout_prepared`
- `command_finished` x4
- `run_completed`
- `l1_promotion_proposed`

Layer 2:
- `run_started`
- `checkout_prepared`
- `command_finished` x5
- `run_completed`
- `l2_decision_proposed`

## What Was Proven

The DB-native path now works for both layers without queue import:
- generator creates `task_requests` and `work_items` directly in the DB
- worker leases and executes those DB-native items
- completed runs can be consumed into reviewable proposal artifacts
- both resulting work items land in `awaiting_review`

This closes the first proof of the internal control-plane loop for:
- Layer 1 generation -> execution -> proposal
- Layer 2 generation -> execution -> decision proposal

## Scope Note

This was an orchestration proof, not a physical-design benchmark:
- the temp repo used stub implementations of:
  - `scripts/run_sweep.py`
  - `npu/eval/run_campaign.py`
  - related report/validation helpers
- the control-plane logic was real
- the workload scripts were intentionally lightweight so the generator/worker/consumer path could be validated quickly

Next recommended step:
- run at least one generator-created item against the real repo workload, not the stub repo, so the DB-native path is exercised with real OpenROAD-facing commands.

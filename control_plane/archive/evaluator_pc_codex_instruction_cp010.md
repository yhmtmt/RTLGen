# Evaluator PC Codex Instruction for CP-010

Archive note:
- historical prompt artifact for an earlier control-plane validation stage
- not part of the current operator workflow

Purpose:
- give a Codex agent on the evaluator machine a concrete, executable runbook,
- keep the shadow control-plane validation off the main checkout,
- require a final report with enough detail to compare against the existing evaluator workflow.

Use this as the user prompt for Codex on the evaluator PC.

## Prompt to Give Codex

```text
Work on /workspaces/RTLGen.

Goal:
- execute the cp-010 shadow control-plane run for the live queue item
  runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json
- do it in a temporary clone, not in the main checkout
- report the result in detail

Read first:
1. control_plane/README.md
2. control_plane/archive/shadow_run_cp010.md
3. notes/evaluation_agent_guidance.md
4. runs/eval_queue/openroad/queued/l2_e2e_softmax_macro_tail_v1.json

Execution rules:
- do not modify the main checkout except for reading files
- do all shadow-run execution in a temp clone under /tmp
- use a fresh sqlite DB in /tmp for the control-plane state
- fetch external models before validate/run if the queue item requires them
- use the current control-plane CLI, not ad hoc scripts, wherever a CLI exists
- if the real physical campaign is too long, do not fake completion; report the exact live state and evidence collected
- if the run reaches a terminal state, run sync-artifacts and inspect the exported evaluated snapshot
- do not open a PR and do not commit temp-clone outputs

Required steps:
1. create a temp clone of /workspaces/RTLGen
2. in the temp clone, run:
   - python3 npu/eval/fetch_models.py --manifest runs/models/onnx_imported_softmax_tail_v1/manifest.json
3. import the live queued item into a fresh control-plane DB
4. execute one worker pass with:
   - platform=nangate45
   - flow=openroad
   - machine_key and hostname set to something concrete for the evaluator machine
5. monitor the worker and determine which of these happened:
   - validate failure
   - run_campaign in progress
   - terminal failed run
   - terminal succeeded run
6. if the run is terminal, run sync-artifacts against that temp DB and temp clone
7. inspect:
   - run status
   - run events
   - per-command stdout/stderr logs
   - exported evaluated snapshot path
   - result field shape
   - metrics_rows shape and count
8. compare the exported result shape with:
   - runs/eval_queue/openroad/evaluated/l2_e2e_onnx_practical_v1_focus_flat_v1.json
9. report the findings back in the final answer

Required report format:

1. Outcome
- one of:
  - succeeded
  - failed
  - still running

2. Execution summary
- temp clone path
- temp DB path
- machine_key
- hostname
- run_key
- whether fetch_models was required and whether it succeeded

3. Control-plane state
- work_item state
- run status
- last run event types in order
- whether sync-artifacts was executed

4. Command results
- for each command attempted:
  - command name
  - exit code or running
  - key stdout/stderr takeaway
  - log file paths

5. Snapshot comparison
- whether an evaluated snapshot was produced
- snapshot path
- result.status
- result.branch
- result.identity_block
- result.metrics_rows type and count
- whether the required evaluated-result fields match the reference shape

6. Blockers or residual issues
- exact missing preconditions, flow failures, or long-running stage

7. Next action
- the single most useful next step

Important:
- if the run is still executing the physical sweep when you stop, do not label it failed
- distinguish clearly between:
  - control-plane failure
  - evaluator precondition failure
  - long-running physical execution
```

## Notes for the Human Operator

- The evaluator machine should have the network access needed for:
  - `python3 npu/eval/fetch_models.py --manifest ...`
- The temp clone is intentional:
  - it avoids modifying the live queue state in the main checkout
  - it keeps the shadow-run evidence isolated
- The long physical phase is expected to take much longer than the control-plane setup path.
- If the Codex run reaches `run_campaign.py` and `run_block_sweep.py` in the temp clone, the control-plane integration is already proven for the live item.

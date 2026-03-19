# Layer 1 Circuit Workflow (Physical Optimization)

## Purpose
Define the operational workflow for Layer 1: parameterized circuit module
generation and physical optimization.

This runbook is the source of truth for module-level search loops. For NPU
architecture-level workflow, use `npu/docs/workflow.md`.

## Scope
- C++ RTLGen module generation (adder/multiplier/MAC/activation/MCM/CMVM/FP).
- Physical synthesis sweeps and PPA/runtime comparison.
- Candidate selection and handoff artifacts for Layer 2.

## Inputs
- Module config JSON (see `examples/about_config.md`).
- Target platform/PDK and sweep parameters.
- Optional baseline design IDs for A/B comparison.

## Outputs
- Per-design RTL + metrics under `runs/designs/<circuit_type>/<design>/`.
- Campaign summaries under `runs/campaigns/<circuit_type>/<campaign>/`.
- Per-PDK candidate handoff manifests under `runs/candidates/<pdk>/`.
- Optional hardened macro artifacts (when needed by Layer 2 hierarchical runs).

## Standard loop
1. Define candidate configs.
2. Generate RTL and sweep physical parameters.
3. Compare PPA/runtime and keep append-only metrics.
4. Select per-PDK candidate set and record rationale.
5. Handoff selected candidates to Layer 2 exploration.

## Execution steps

### 1) Build generator
```sh
mkdir -p build
cd build
cmake ..
cmake --build .
```

### 2) Generate a module RTL candidate
```sh
build/rtlgen examples/config.json
```

Row-wise softmax example:
```sh
build/rtlgen examples/config_softmax_rowwise_int8.json
```

### 3) Run physical sweep
Use the flow wrappers that write into `runs/designs/`:
```sh
python3 scripts/generate_design.py <config.json> <platform>
python3 scripts/run_sweep.py \
  --configs <config_or_config_list> \
  --platform <platform> \
  --sweep <sweep.json> \
  --out_root runs/<circuit_type>
```

Row-wise softmax seed sweep:
```sh
python3 scripts/run_sweep.py \
  --configs \
    examples/config_softmax_rowwise_int8.json \
    examples/config_softmax_rowwise_int8_r8_acc20.json \
    examples/config_softmax_rowwise_int8_r8_shift5.json \
  --platform nangate45 \
  --sweep runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json \
  --out_root runs/designs/activations
```

### 4) Aggregate and inspect
```sh
python3 scripts/build_runs_index.py
```
- Browser view: `docs/runs/index.html`
- Keep `metrics.csv` append-only; do not rewrite prior runs.

### 5) Select and hand off to Layer 2
- Record preferred per-PDK module variants and parameter ranges.
- For hierarchical NPU integration, provide:
  - design/config identity (`config_hash`, key parameters),
  - candidate `evaluation_scope` (`wrapped_io` vs `macro_hardened`),
  - hardened macro views (`macro_manifest.json`) and selection rules for
    entries marked `macro_hardened`.

### Wrapper-vs-macro policy
- If a candidate is evaluated only as a wrapper with IO registers, mark it as
  `evaluation_scope=wrapped_io`.
- For hierarchical top-level usage claims, re-evaluate the candidate as a
  hardened macro and publish `evaluation_scope=macro_hardened` plus
  `macro_manifest`.

## Data hygiene
- Keep committed artifacts lightweight (configs, RTL, `metrics.csv`, summaries).
- Do not commit large temporary logs or DEF/GDS.
- Preserve reproducibility with stable design names, tags, and parameter hashes.

## Remote execution

### Default path: DB-native `l1_sweep`
Use the control plane as the default execution path for new Layer 1 physical
evaluation items.

Generate a DB-backed Layer 1 work item:
```sh
PYTHONPATH=/workspaces/RTLGen/control_plane \
python3 -m control_plane.cli.main generate-l1-sweep \
  --database-url "$RTLCP_DATABASE_URL" \
  --repo-root /workspaces/RTLGen \
  --sweep-path runs/designs/activations/sweeps/nangate45_softmax_rowwise_v1.json \
  --configs examples/config_softmax_rowwise_int8.json examples/config_softmax_rowwise_int8_r8_acc20.json \
  --platform nangate45 \
  --out-root runs/designs/activations \
  --requested-by @yhmtmt \
  --proposal-id <proposal_id> \
  --proposal-path docs/developer_loop/<proposal_id>
```

Then use the normal operator flow:
1. worker executes the `l1_sweep` item from the DB
2. completion service syncs allowlisted evidence
3. submission service opens the evaluation PR
4. review the PR and merge valid evidence
5. consume Layer 1 result if needed:
   ```sh
   PYTHONPATH=/workspaces/RTLGen/control_plane \
   python3 -m control_plane.cli.main consume-l1-result \
     --database-url "$RTLCP_DATABASE_URL" \
     --repo-root /workspaces/RTLGen \
     --item-id <l1_item_id>
   ```

Recommended bookkeeping:
- record DB-created item ids in
  `docs/developer_loop/<proposal_id>/evaluation_requests.json`
- treat the evaluation PR as the evidence boundary, same as Layer 2

### Legacy/manual fallback: file queue JSON
The file queue under `runs/eval_queue/openroad/queued/` is still readable as a
manual evaluator handoff format, but it is now a fallback path rather than the
default for new items.

Use it only when:
- DB-backed operator services are unavailable
- you need a manual/offline handoff to an external evaluator
- you are preserving an older historical lane for comparison

Legacy references:
- template:
  - `runs/eval_queue/openroad/templates/item_template.json`
- historical Layer 1 seed sweep result:
  - `runs/eval_queue/openroad/evaluated/l1_softmax_rowwise_candidates_nangate45_v1.json`
- historical macro-hardening item:
  - `runs/eval_queue/openroad/evaluated/l1_macro_harden_softmax_rowwise_r4_nangate45_v1.json`

Legacy manual evaluator workflow:
1. Create branch `eval/<item_id>/<session_id>` on high-performance machine.
2. Execute commands listed in the item.
3. Commit lightweight outputs (`metrics.csv`, manifests, config updates).
4. Move item to `runs/eval_queue/openroad/evaluated/` and fill `result`.
5. Open PR and run `python3 scripts/validate_runs.py`.

## Related docs
- Two-layer split and interaction: `docs/two_layer_workflow.md`
- Artifact layout and contribution rules: `runs/README.md`
- Cross-project concepts/history: `notes/workflow.md`
- Layer 2 NPU workflow: `npu/docs/workflow.md`

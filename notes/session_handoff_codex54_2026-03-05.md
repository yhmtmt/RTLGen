# Session Handoff for Codex 5.4 Upgrade (2026-03-05)

## Snapshot
- Timestamp (UTC): `2026-03-05`
- Repo: `yhmtmt/RTLGen`
- Branch: `master`
- HEAD: `2052123` (`eval: add onnx_practical_v1 model set and reuse campaign`)
- Sync state: `master` is aligned with `origin/master`.
- Known local dirt (intentional/ignored): submodule marker on `third_party/flopoco`.

## What Was Completed
- Merged evaluator PR #8 on `2026-03-05`:
  - focused flat rerun for `mlp_smoke_v2`
  - merge commit: `8f66baf720557bbdf454a4c5fcf372c0e1df8d1c`
- Merged evaluator PR #9 on `2026-03-05`:
  - focused hier rerun for `mlp_smoke_v2`
  - merge commit: `76a8082efbd7af1b494e3afe29a51d1edeac242e`
- Bootstrapped practical model/campaign layer:
  - model set: `runs/models/onnx_practical_v1/`
  - campaign: `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/`
  - baseline run/report completed (no OpenROAD rerun).

## Queue Status
- `runs/eval_queue/openroad/queued/` is empty (`.gitkeep` only).
- Latest evaluated items include:
  - `l2_e2e_mlp_smoke_v2_focus_flat_v1.json`
  - `l2_e2e_mlp_smoke_v2_focus_hier_v1.json`

## Current Campaign State

### 1) `mlp_smoke_v2_reuse` (post flat+hier focused reruns)
- Campaign dir: `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/`
- Sample balance: `30` for all 4 `(arch_id, macro_mode)` aggregate points.
- Ranking remains:
  1. `fp16_nm1 + flat_nomacro`
  2. `fp16_nm1 + hier_macro`
  3. `fp16_nm2 + flat_nomacro`
  4. `fp16_nm2 + hier_macro`

### 2) `onnx_practical_v1_reuse` (new baseline)
- Campaign dir: `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/`
- Results rows: `60`
- Models: `mlp_p1`, `mlp_p2`, `mlp_p3`
- Aggregate sample_count: `15` per `(arch_id, macro_mode)` point
- Ranking (balanced profile):
  1. `fp16_nm1 + flat_nomacro`
  2. `fp16_nm1 + hier_macro`
  3. `fp16_nm2 + flat_nomacro`
  4. `fp16_nm2 + hier_macro`
- Split-path signal in notes:
  - `mapper_split_enabled=1` rows: `40`
  - `mapper_split_enabled=0` rows: `20`

## New Artifacts Added
- Model set:
  - `runs/models/onnx_practical_v1/manifest.json`
  - `runs/models/onnx_practical_v1/README.md`
  - `runs/models/onnx_practical_v1/mlp_p1.onnx`
  - `runs/models/onnx_practical_v1/mlp_p2.onnx`
  - `runs/models/onnx_practical_v1/mlp_p3.onnx`
- Campaign:
  - `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json`
  - `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/README.md`
  - `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/objective_profiles.json`
  - plus baseline outputs under that campaign directory.

## Validations Last Run
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse/campaign.json --check_paths`
- `python3 scripts/validate_runs.py`

## Recommended Immediate Next Steps (after upgrade)
1. Enqueue focused OpenROAD rerun for `onnx_practical_v1` flat mode:
   - `--modes flat_nomacro --repeat 10 --jobs 2`
2. Merge evaluator PR, then enqueue complementary hier mode rerun:
   - `--modes hier_macro --repeat 10 --jobs 2`
3. Compare balanced 30/30 sample outcomes and decide default mode policy.

## Recovery Commands
```sh
cd /workspaces/RTLGen
git pull --ff-only
git status --short --branch
python3 scripts/validate_runs.py
```

If continuing from queue flow:
```sh
ls -la runs/eval_queue/openroad/queued runs/eval_queue/openroad/evaluated
```

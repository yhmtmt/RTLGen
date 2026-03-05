Runs Model Sets
===============

Purpose
-------
Shared ONNX benchmark model sets for campaign-level evaluation.

Contract
--------
Each model set lives under `runs/models/<model_set_id>/` and must provide a
`manifest.json` with:
- `version` (0.1)
- `model_set_id`
- `models[]` entries: `model_id`, `onnx_path`, `onnx_sha256`

Campaigns reference model sets via:
- `model_set_id`
- `model_manifest`

This keeps model provenance traceable in `results.csv` and result-row JSON.

Versioning policy
-----------------
- Treat each benchmark-set revision as a new `model_set_id` directory.
- Keep prior model sets immutable once used in merged campaign results.
- Launch a new campaign per benchmark-set revision to preserve historical
  comparability.

Current sets
------------
- `mlp_smoke_v0`: initial smoke set for Layer2 bring-up.
- `mlp_smoke_v1`: revisioned smoke set used to bootstrap physical-reuse
  campaign flow (`runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/`).
- `mlp_smoke_v2`: scaled smoke set (`mlp3`/`mlp4` presets) paired with
  `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/`.

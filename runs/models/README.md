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
- optional `models[].fetch` metadata when the ONNX binary is intentionally not
  stored in the repo:
  - `url` (required): `http://`, `https://`, or `file://`
  - `mirrors[]` (optional)
  - `notes`, `license` (optional)

Campaigns reference model sets via:
- `model_set_id`
- `model_manifest`

This keeps model provenance traceable in `results.csv` and result-row JSON.
When `models[].fetch` is present, evaluators should materialize the binary into
`onnx_path` with:

```sh
python3 npu/eval/fetch_models.py --manifest runs/models/<model_set_id>/manifest.json
```

The fetched file must still match `onnx_sha256`.

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
- `onnx_practical_v1`: practical-scale benchmark set (larger MLP proxies)
  paired with `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/`.
- `onnx_practical_v1_fetch_mirror_v1`: cache-backed external-fetch mirror of
  the practical MLP proxy set, paired with
  `runs/campaigns/npu/e2e_eval_onnx_practical_v1_fetch_mirror_num_modules_v1/`.
- `onnx_imported_mlp_v1`: broader imported ONNX MLP set fetched from upstream
  GitHub repos into `runs/model_cache/`, paired with
  `runs/campaigns/npu/e2e_eval_onnx_imported_mlp_num_modules_v1/`.
- `onnx_imported_softmax_tail_v1`: imported classifier-tail set with a real
  terminal `Softmax` path, paired with
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/`.
- `llm_smoke_v1`: benchmark-contract-defined tiny attention proxy set for
  LLM-oriented evaluation. This is the first runnable non-terminal-`Softmax`
  smoke set and now includes deterministic numerical reference fixtures under
  `runs/models/llm_smoke_v1/reference_manifest.json`; it should still be
  treated as scheduler/reference bring-up, not final LLM accuracy evidence;
  see `docs/architecture/llm_attention_benchmark_ladder.md`.

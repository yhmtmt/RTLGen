Runs Model Cache
================

Purpose
-------
Evaluator-local cache for large or externally hosted model binaries that should
not be tracked in Git.

Usage
-----
- Model manifests may point `onnx_path` into `runs/model_cache/...`.
- Evaluators materialize files with:

```sh
python3 npu/eval/fetch_models.py --manifest runs/models/<model_set_id>/manifest.json
```

- The fetched file must still match the manifest `onnx_sha256`.

Notes
-----
- Contents under this directory are ignored by Git.
- Keep only reproducible cache artifacts here; manifests and campaign metadata
  stay under `runs/models/` and `runs/campaigns/`.

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

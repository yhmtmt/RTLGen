# NPU Evaluation Contract (System-Level)

## Purpose
This directory defines the contract for end-to-end NPU evaluation campaigns:
- ONNX model mapping inputs
- physical mapping (OpenROAD) outputs
- performance simulation outputs
- merged PPA + model-level metrics rows
- benchmark/model-set provenance (`model_set_id`, ONNX SHA256)

It is the first step toward a reproducible closed-loop flow:
`ONNX -> mapper -> physical -> perf -> report`.

## Files
- `npu/eval/contract.md`: human-readable contract and field definitions.
- `npu/eval/campaign.schema.json`: JSON schema for campaign manifests.
- `npu/eval/result_row.schema.json`: JSON schema for merged result rows.
- `npu/eval/validate.py`: lightweight validator for campaign/result JSON.
- `npu/eval/examples/`: minimal examples.
- `runs/models/<model_set_id>/manifest.json`: shared benchmark model-set
  manifest with ONNX SHA256 checksums.
- `npu/eval/decoder_backend.py`: pluggable decoder backend interface for decoder-quality evaluation (`placeholder_v1`, frozen-artifact `replay_v1`, and external `command_json_v1`).
- `npu/eval/gen_llm_decoder_reference_suite.py`: generate reference-only
  decoder fixtures for the tiny decoder-quality stage.
- `npu/eval/gen_llm_decoder_candidate_suite.py`: generate candidate decoder
  fixtures for the tiny decoder-quality stage.
- `npu/eval/compare_llm_decoder_quality.py`: summarize token-level exact-match
  rates from decoder reference/candidate manifests.
- `npu/eval/run_llm_decoder_onnx_reference.py`: optional exact-reference runner
  behind `command_json_v1` for a future pinned decoder ONNX export.

The repo can now express a future exact-reference pair explicitly even before the
assets are present: the model contract may point at a `reference_onnx_binding.json`
that locks the intended ONNX path, tokenizer bundle, runtime, and fetch-plan
provenance. The current planned first exact-reference source is `sshleifer/tiny-gpt2` with the GPT-2 tokenizer family, but that remains inactive until fetched and hashed.

The decoder-quality scaffold also introduces separate non-ONNX contracts for:
- datasets: `runs/datasets/...`
- tokenizers: `runs/tokenizers/...`
- placeholder decoder model bindings: `runs/models/<model_id>/model_contract.json`

## Validation
Validate campaign manifest:
```sh
python3 npu/eval/validate.py --campaign npu/eval/examples/minimal_campaign.json
```

Validate merged result row:
```sh
python3 npu/eval/validate.py --result-row npu/eval/examples/minimal_result_row.json
```

Optionally verify path-like fields exist:
```sh
python3 npu/eval/validate.py --campaign <campaign.json> --check_paths
```

If the referenced model manifest uses external fetch metadata, materialize the
ONNX files first:
```sh
python3 npu/eval/fetch_models.py --manifest runs/models/<model_set_id>/manifest.json
```
Then rerun `--check_paths`.

Reuse-oriented campaign example:
```sh
python3 npu/eval/validate.py \
  --campaign runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json \
  --check_paths
```

## Campaign Runner (Phase-2 Scaffold)
Run mapper + perf and merge with physical metrics into append-only results CSV:
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
If a model file declared in the manifest is missing locally, the runner now
fails early with a fetch hint instead of falling through to mapper errors.
The runner honors optional per-architecture `physical_select` filters in the
campaign (`compare_group`, `tag_prefix`) and encodes physical `param_hash` into
`run_id` as stable design-point identity across sweep variants.
Each emitted row also includes `sample_id`/`batch_id`/`sample_index` so
statistical reruns can coexist without overloading `run_id`.
Row `notes` include mapper split metadata keys for quick filtering:
`mapper_split_enabled`, `mapper_split_chunk_count`, `mapper_split_chunks`.
Each campaign must also declare `model_set_id` and `model_manifest`
(`runs/models/<set>/manifest.json`), and emitted rows include
`model_set_id`/`model_manifest`/`onnx_sha256` for traceability.
Use a distinct campaign per benchmark set revision (do not silently mutate
model membership inside one campaign ID).
Model manifests may keep large ONNX binaries out of the repo by attaching an
optional `fetch` object to each model entry. The fetch tool materializes the
file into `onnx_path` while preserving the existing `onnx_sha256` provenance
contract.
When `architecture_points[].layer1_modules` is set, campaign validation checks
selected candidate IDs against `runs/candidates/...` manifests and rejects
`wrapped_io` candidates unless `allow_wrapped_io=true` is explicitly set.
It reuses existing per-model mapper/perf artifacts under
`<campaign_dir>/artifacts/` when input metadata matches; force full rerun with
`--no_reuse_model_artifacts`.
Use `--jobs <N>` to parallelize model-level mapper/perf generation when running
multiple models in one campaign.
Use `--batch_id <label>` to tag rerun batches explicitly (optional).
Use campaign field `physical_source_campaign` to record which prior campaign
provided baseline physical settings/results context for reuse runs.

If physical rows are missing in `<design_dir>/metrics.csv`, allow runner to
invoke the sweep:
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --run_physical
```

Dry-run (print commands only):
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --dry_run
```

## Campaign Reporting
Generate per-model summaries and aggregate ranking from merged CSV:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
The report step also emits:
- `summary.csv` (all model + aggregate summaries)
- `pareto.csv` (non-dominated aggregate points by latency/energy/runtime)
- `best_point.json` (weighted-objective best point)

Optional objective weights:
```sh
python3 npu/eval/report_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --w_latency 1.0 --w_energy 1.0 --w_runtime 0.2
```

## Objective Profile Sweep
Run multiple objective profiles and collect best-point recommendations:
```sh
python3 npu/eval/optimize_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json \
  --profiles_json runs/campaigns/npu/e2e_eval_v0/objective_profiles.json
```
Outputs:
- `objective_sweep.csv`
- `objective_sweep.md`
- per-profile reports under `objective_profiles/<profile>/`

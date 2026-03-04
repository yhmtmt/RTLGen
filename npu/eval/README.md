# NPU Evaluation Contract (System-Level)

## Purpose
This directory defines the contract for end-to-end NPU evaluation campaigns:
- ONNX model mapping inputs
- physical mapping (OpenROAD) outputs
- performance simulation outputs
- merged PPA + model-level metrics rows

It is the first step toward a reproducible closed-loop flow:
`ONNX -> mapper -> physical -> perf -> report`.

## Files
- `npu/eval/contract.md`: human-readable contract and field definitions.
- `npu/eval/campaign.schema.json`: JSON schema for campaign manifests.
- `npu/eval/result_row.schema.json`: JSON schema for merged result rows.
- `npu/eval/validate.py`: lightweight validator for campaign/result JSON.
- `npu/eval/examples/`: minimal examples.

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

## Campaign Runner (Phase-2 Scaffold)
Run mapper + perf and merge with physical metrics into append-only results CSV:
```sh
python3 npu/eval/run_campaign.py \
  --campaign runs/campaigns/npu/e2e_eval_v0/campaign.json
```
The runner honors optional per-architecture `physical_select` filters in the
campaign (`compare_group`, `tag_prefix`) and encodes physical `param_hash` into
`run_id` as stable design-point identity across sweep variants.
Each emitted row also includes `sample_id`/`batch_id`/`sample_index` so
statistical reruns can coexist without overloading `run_id`.
When `architecture_points[].layer1_modules` is set, campaign validation checks
selected candidate IDs against `runs/candidates/...` manifests and rejects
`wrapped_io` candidates unless `allow_wrapped_io=true` is explicitly set.
It reuses existing per-model mapper/perf artifacts under
`<campaign_dir>/artifacts/` when input metadata matches; force full rerun with
`--no_reuse_model_artifacts`.
Use `--jobs <N>` to parallelize model-level mapper/perf generation when running
multiple models in one campaign.
Use `--batch_id <label>` to tag rerun batches explicitly (optional).

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

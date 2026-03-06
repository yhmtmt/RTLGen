# NPU End-to-End Evaluation Contract (Draft v0.1)

## Purpose
Define a stable contract for system-level evaluation so architecture sweeps can
be compared across:
- physical mapping quality/runtime
- model-level performance
- aggregated PPA/perf objectives

## Scope
- Campaign-level inputs (models + architecture points + tool configs)
- Per-run merged result row schema
- Validation rules before running expensive flows

## 1) Campaign Manifest
A campaign JSON declares:
- `campaign_id`, `model_set_id`, `model_manifest`, `platform`, `make_target`,
  `repeats`
- model list (`models[]`) with ONNX paths and mapper/perf profiles
  - model IDs/paths must match entries in `model_manifest`
  - ONNX file hashes in `model_manifest` are validation targets
  - model-manifest entries may optionally add `fetch` metadata so evaluators
    can materialize large ONNX binaries locally instead of tracking them in
    the repo
- architecture list (`architecture_points[]`) with design directories, sweeps,
  and macro manifests/libraries
  - optional `layer1_modules` per architecture point:
    - `manifest`: `runs/candidates/<pdk>/module_candidates.json`
    - `variant_ids`: selected Layer 1 candidate IDs
    - `allow_wrapped_io` (default false): explicit override to allow
      wrapper-level (`evaluation_scope=wrapped_io`) candidates
  - optional `physical_select` per architecture point:
    - `compare_group`
    - `tag_prefix`
    These constrain which `metrics.csv` rows are eligible for merge.
- optional `physical_source_campaign`:
  - campaign path used when reusing existing physical samples for additional
    model benchmarking (no OpenROAD rerun intent)
- output locations for merged reporting

This file is the single source of truth for what should be evaluated.
Different benchmark sets/revisions should be tracked as different campaigns
(`campaign_id`) even when architecture points are unchanged.
When `model_manifest.models[].fetch` is present, evaluators should run
`python3 npu/eval/fetch_models.py --manifest <manifest.json>` before
`validate.py --check_paths` or `run_campaign.py`.

## 2) Merged Result Row
A merged result row represents one evaluated point:
- keys: `campaign_id`, `run_id`, `model_id`, `arch_id`, `macro_mode`
  - `run_id`: stable design-point identity (includes physical `param_hash`).
  - `sample_id`: unique sample-row identity for statistical reruns.
  - `batch_id`: executor-provided rerun batch label.
  - `sample_index`: per-`run_id` sample sequence index.
  - `model_set_id`, `model_manifest`, `onnx_sha256`: benchmark provenance.
  - optional `mapper_arch_hash`, `perf_config_hash`: tool-input provenance.
- physical metrics:
  - `critical_path_ns`
  - `die_area_um2`
  - `total_power_mw`
  - `flow_elapsed_s`
  - `place_gp_elapsed_s`
- performance metrics:
  - `cycles`
  - `latency_ms`
  - `throughput_infer_per_s`
  - `energy_mj`
- artifact pointers:
  - `synth_result_json`
  - `perf_trace_json`
  - `schedule_yml`
  - `descriptors_bin`

Rows are append-only and become the canonical input for downstream Pareto or
recommendation reports.
`notes` may include additional key-value provenance; current runner emits
mapper split tags (`mapper_split_enabled`, chunk count/list) for direct
split-vs-non-split filtering in CSV analysis.

## 3) Validation Rules (v0.1)
- IDs must be non-empty and unique within each list.
- `repeats >= 1`.
- `macro_mode` must be one of: `flat_nomacro`, `hier_macro`.
- If an ONNX file is intentionally absent from the repo, its manifest entry
  must provide valid `fetch.url` metadata; otherwise validation fails even
  without `--check_paths`.
- If `layer1_modules` is set, selected candidate IDs must exist in the
  manifest and match campaign platform.
- `wrapped_io` candidates are rejected unless `allow_wrapped_io=true` is set
  explicitly on that architecture point.
- If `status=ok`, merged metrics must be numeric and non-negative.
- Optional `--check_paths` verifies file paths exist on disk.

## 4) Near-Term Execution Plan
1. **Contract lock** (this step):
   - add campaign + result-row schema and validator
   - create initial campaign manifest for target ONNX models
2. **Runner scaffolding**:
   - one orchestrator command to execute mapping, physical, and perf stages
3. **Physical-to-perf feedback**:
   - use physical timing/power in perf-derived latency/energy rows
4. **Model-set reporting**:
   - generate per-model + aggregate PPA/perf reports from merged rows

## Notes
- This contract does not replace existing per-tool inputs (mapper schedule,
  OpenROAD sweeps, perf config). It normalizes them at campaign/report level.

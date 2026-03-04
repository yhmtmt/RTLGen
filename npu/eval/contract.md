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
- `campaign_id`, `platform`, `make_target`, `repeats`
- model list (`models[]`) with ONNX paths and mapper/perf profiles
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
- output locations for merged reporting

This file is the single source of truth for what should be evaluated.

## 2) Merged Result Row
A merged result row represents one evaluated point:
- keys: `campaign_id`, `run_id`, `model_id`, `arch_id`, `macro_mode`
  - `run_id`: stable design-point identity (includes physical `param_hash`).
  - `sample_id`: unique sample-row identity for statistical reruns.
  - `batch_id`: executor-provided rerun batch label.
  - `sample_index`: per-`run_id` sample sequence index.
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

## 3) Validation Rules (v0.1)
- IDs must be non-empty and unique within each list.
- `repeats >= 1`.
- `macro_mode` must be one of: `flat_nomacro`, `hier_macro`.
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

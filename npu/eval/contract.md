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
- output locations for merged reporting

This file is the single source of truth for what should be evaluated.

## 2) Merged Result Row
A merged result row represents one evaluated point:
- keys: `campaign_id`, `run_id`, `model_id`, `arch_id`, `macro_mode`
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

# NPU Status Summary

## Purpose
Single-page snapshot of NPU development status for quick reference.

<!-- STATUS_META_START -->
Last updated: 2026-03-06
Git: d76a23b
<!-- STATUS_META_END -->

## Current status
- **Shell/ABI (Implemented)**: v0.1 MMIO/CQ/DMA semantics are documented and
  exercised in RTL benches.
- **RTLGen core path (Implemented)**: generator emits `top.v`, `mmio_map.vh`,
  `sram_map.vh`, and optional AXI-Lite wrapper.
- **Mapper (Implemented)**: schedule IR + binary descriptor emission are active
  in `npu/mapper/`.
- **Mapper split phase-1 (Implemented)**: oversized MLP `GEMM2`
  weight-SRAM cases now lower via output-channel chunking with
  `mapper_notes.gemm2_*` provenance propagated into campaign rows.
- **RTL simulation (Implemented)**: golden regression covers DMA/GEMM/VEC/event
  paths with RTL logs consumed by compare scripts.
- **Performance simulation (Implemented)**: descriptor-driven analytical model
  plus unit tests and RTL/perf comparison hooks.
- **SRAM PPA (Implemented)**: CACTI-based flow and aggregation pipeline are available.
- **OpenROAD block flow (Implemented)**: `run_block_sweep.py` wrapper is active.
- **fp16 backend sweep (Implemented)**: `make_target=finish` comparison completed:
  - `builtin_raw16`: `critical_path_ns=5.4287`, `die_area=2250000`, `total_power_mw=0.233`
  - `cpp_ieee`: `critical_path_ns=5.6462`, `die_area=2250000`, `total_power_mw=0.229`
  - report: `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`
- **fp16 backend lock (Implemented)**: generator default for
  `compute.gemm.mac_type=fp16` is `mac_source=rtlgen_cpp` (IEEE-half path);
  `builtin_raw16` remains explicit non-IEEE baseline.
- **Architecture layering v0.2 draft (Implemented)**: draft schema + example and
  `npu/arch/to_rtlgen.py` derivation path are active for `gemm`/`vec` candidate
  emission.
- **SRAM pre-synthesis flow (Implemented)**: `npu/synth/pre_synth_memory.py`
  selects memgen when configured and falls back to CACTI estimation.
- **System-level eval flow scaffold (Implemented)**: campaign contract +
  validator (`npu/eval/validate.py`), orchestrator
  (`npu/eval/run_campaign.py`), reporting/ranking
  (`npu/eval/report_campaign.py`), and objective-profile sweep
  (`npu/eval/optimize_campaign.py`) are active with evaluator-side external
  model fetch support (`npu/eval/fetch_models.py`), the scaffold
  `runs/campaigns/npu/e2e_eval_v0/` and active reuse campaigns
  `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/` and
  `runs/campaigns/npu/e2e_eval_onnx_practical_v1_reuse_num_modules_v1/`.
- **External-fetch bootstrap set (Implemented)**:
  `runs/models/onnx_practical_v1_fetch_mirror_v1/` and
  `runs/campaigns/npu/e2e_eval_onnx_practical_v1_fetch_mirror_num_modules_v1/`
  prove the evaluator-side fetch/cache flow end-to-end. The mirrored report
  matches the repo-tracked practical baseline exactly.
- **Campaign baselines (Implemented)**: `mlp_smoke_v2_reuse` is balanced at
  30 samples per `(arch_id, macro_mode)` point after focused flat/hier reruns;
  `onnx_practical_v1_reuse_num_modules_v1` is the active practical baseline
  with balanced coverage across all four `(arch_id, macro_mode)` aggregate
  points and corrected `num_modules`-aware mapper/perf artifacts across
  `mlp_p1`, `mlp_p2`, and `mlp_p3`.
- **Practical default policy (Locked)**: use `flat_nomacro` as the default
  physical mode for the current `onnx_practical_v1` baseline. Under the
  balanced objective, `fp16_nm2 + flat_nomacro` is the leading practical
  point because row-parallel lowering converts `compute.gemm.num_modules=2`
  into lower model latency. `fp16_nm1 + flat_nomacro` remains the best
  energy-only / broader-PPA point.

## In progress
- C++ MAC generator extension for explicit MAC operation modes including
  accumulator feedback (`pp_row_feedback`) for NPU exploration.
- Expanded vector-op constrained-random coverage for activation and derivative ops.
- Mapper scale-out beyond phase-1 MLP `GEMM2` output chunking.
- Broaden validation of the `num_modules`-aware mapper/perf contract beyond the
  current practical MLP proxy set and confirm the objective-weight policy for
  default architecture selection.
- Replace the current external-fetch bootstrap mirror with a broader imported
  ONNX benchmark set, then rerun the practical campaign on it.
- Stronger `arch v0.2` validation (types/ranges/enums) and mapper/perf usage of
  interconnect + mapping constraints.
- Post-physical SRAM metric extraction and feedback loop into perf simulation.

## Planned
- Broader compute-enabled OpenROAD sweeps (beyond fp16 backend comparison).
- Additional numeric-policy hardening and stress tests for fp16 edge behavior.
- Optional future datatype exploration (bf16/fp8) after fp16 path maturity.

## Pointers
- Index: `npu/docs/index.md`
- Workflow: `npu/docs/workflow.md`
- Simulation plan: `npu/docs/sim_dev_plan.md`
- Synthesis plan: `npu/synth/plan.md`

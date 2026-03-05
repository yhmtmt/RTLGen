Log
===

2025-11-26 — Initialization
- Papers not yet provided; proceed with repo `README.md` files and mark this dependency for later ingestion.
- Action plan drafted in `plan/README.md`.
- Read `README.md`: RTLGen generates Verilog from JSON configs, currently focused on multipliers; build via CMake with GoogleTest + OR-Tools; devcontainer sets toolchain (incl. OpenROAD) per `development.md`; run `rtlgen <config>` using examples/about_config guidance; includes Booth vs normal multiplier comparison in `notes/booth4_vs_normal/...`.
- Read `json/README.md`: vendored nlohmann/json (single-header JSON lib) with extensive API docs, examples, and test guidance; treat as third-party dependency unless customization is needed.
- Read `development.md`: devcontainer supplies OpenROAD/toolchain; xhost tip for GUI flows; scripts: `execute_evaluation.py` (legacy) and newer `generate_design.py` + `run_autotuner.py` to prep/run OpenROAD flow with tunable params; bugfix-autotuner.patch applied during container build; pinned ORFS/OR versions; sample GDS2 stored in `materials/sample_gds2.png`.
- Read `examples/about_config.md`: config schema v1.1 supports multi-operation; operands array carries name/dim/width/signed; operations types include adder, multiplier, multiplier_yosys, mcm, cmvm; PPG options Normal/Booth4, compressor fixed to ILP-based AdderTree, CPA choices Ripple/KoggeStone/BrentKung/Sklansky; pipeline depth currently fixed to 1; MCM/CMVM options for heuristic/ILP engines and matrices; legacy v1.0 layout still accepted.
- Read `notes/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md`: OpenROAD Nangate45 comparison of Booth vs normal PPG with ILP compressor and RCA; results show similar delay/area, Booth offers no clear advantage; recaps Booth glitch/power concerns; references UFO-MAC and PrefixRL as potential future optimizations.
- Moved `constant_multiplication.md` to `notes/constant_multiplication.md` and linked it from `examples/about_config.md`; doc covers MCM/CMVM algorithms (BHA/BHM/RAG-n/H_cub, ILP, H2MC/H_CMVM) and CLI usage/tests.
- Toolchain check: `cmake --build build` completes (targets constant_multiplication, rtlgen, tests, MCM/CMVM CLIs). Smoke test: ran `build/rtlgen examples/config.json` in `/tmp` → multiplier generated successfully.
- Tests: `ctest --output-on-failure` now passes all targets after restoring Verilog testbenches (`tests/fir3_mcm_tb.v`, `tests/dct4_cmvm_tb.v`) used by `test_verilog_mcm_and_cmvm`.
- OpenROAD prep: unpacked bundled onnxruntime to `third_party/onnxruntime-linux-x64-1.23.1` and set `LD_LIBRARY_PATH` for CLI runs. `scripts/generate_design.py examples/config.json nangate45 --force_gen true` succeeded, placing design files under `/orfs/flow/designs/.../booth_multiplier32s_wrapper`. Autotuner invocation (`openroad_autotuner ... tune`) failed inside Ray init with `PermissionError: Operation not permitted` when creating a socket (likely sandbox restriction).
- Manual autotuner run (user): `booth_multiplier32s_wrapper.csv` captured PPA tradeoffs. Highlights: best metric 1.0 at coeffs (P=0.25,A=0.5,Po=0.25) and (P=0.5,A=0,Po=0.5) with clk 5.3834ns, area 7206.05, power 0.00155171. Fastest clk 2.8981ns at (P=0.25,A=0.75,Po=0) with same area/power as above. Smallest area 3200.57 at (P=0,A=1,Po=0) with clk 8.4281ns; lowest power 0.000888046 at (P=0,A=0,Po=1) with clk 9.4081ns.
- Added skew-aware prefix adder option (`SkewAwarePrefix`) with optional `input_delays` parsing, generator implementation, doc update, and Verilog regression in `test_adder` (8-bit skewed case).

2025-12-02 — FloPoCo/PAGSuite integration for FP ops
- Added `pagsuite` and `flopoco` as submodules to enable variable floating-point operation generators (adder/mul/FMA). CMake now vendors PAGSuite via `ExternalProject` before building FloPoCo, installing into `third_party/*-install` and copying the FloPoCo binary to `bin/flopoco`.
- During FloPoCo build a local patch is auto-applied (git-hash stringification guard; ScaLP-dependent ternary SCM guarded). Without ScaLP the “optimal” shift/add constant-mult operators stay disabled; other cores still build. Dependencies expected: GMP/MPFR/MPFI, LAPACK/BLAS, Sollya; PAGSuite supplied in-tree; ScaLP still optional/missing.
- RTLGen now parses `kind: "fp"` operands with `fp_format` (total_width + mantissa_width) and supports `fp_mul` operations by invoking FloPoCo (`FPMult`) then Yosys+GHDL to emit Verilog; iverilog is run for a syntax check of the generated Verilog. Added usage notes to `examples/about_config.md`.

2025-12-04 — Generator review and optimization opportunities
- Current coverage: integer multipliers with Normal/Booth PPG, ILP-placed FA/HA compressor tree (UFO-MAC style), CPAs (Ripple, KoggeStone, BrentKung, Sklansky, SkewAware with input-delay awareness), constant-mult (MCM/CMVM) via heuristics/ILP, activations (int ReLU/ReLU6/leaky/PWL; FP ReLU/leaky), and FloPoCo-based FP add/mul/FMA path (Yosys+GHDL emitted). No memories/NoC/system-level generators yet.
- Gate-level: compressor tree only uses 3:2/2:2 cells; add 4:2/5:2/6:2 compressors and size-aware prefix cells to shave stages/fanout. Objective: >8–10% Fmax gain on 32-bit multiplier in Nangate45 at ≤+3% area vs current ILP layout.
- Partial-circuit: pipeline depth fixed to 1; extend config to place pipeline regs in CT/CPA (and carry them through ILP) plus optional Booth low-power variant for signed path. Objectives: hit <3.0ns clk on 32-bit multiplier with ≤5% area increase; show ≥10% dynamic power drop when low-power Booth is enabled on signed cases.
- Architecture level: no integer MAC/accumulate tree or SIMD/vector blocks. Add MAC generator (w/ optional activation) and multi-operand reduction tree reusing CT/CPA. Target: throughput ≥2x vs repeated adders for 8-lane dot product and timing parity with standalone multiplier.
- Memory hierarchy: absent. Add simple banked SRAM/register-file/cache wrappers (OpenRAM or behavioral) sized from workload descriptors. Objective: sustain ≥90% utilization for 8-lane MAC array on GEMV-like traffic with <10% area overhead vs compute.
- NoC/communication: absent. Provide parameterized bus/mesh/crossbar with flow-control hooks to feed compute tiles. Objective: demonstrate bandwidth to keep ≥2 MAC tiles saturated on synthetic burst/stride patterns with <1% additional latency per hop in 45nm flow.
- Network-level: no end-to-end NPU harness. Build config-driven pipeline (model loader + precision/tile scheduler + simulation hooks for area/timing/power) to compare generator variants. Objective: produce baseline perf/energy reports on a small CNN/MLP and track deltas as optimizations land.
- Evaluation flow (non-autotuner): added `scripts/run_sweep.py` to sweep OpenROAD parameters serially using `generate_design.py` outputs, tagging runs to isolate reports. Per-run SDC is emitted with the requested clock, results parsed from `6_finish.rpt`/`6_final.def`, and indexed into `runs/index.csv` for ML ingestion. Example grid lives in `scripts/sweep_example.json`.

2025-12-15 — Prefix adder sweep (Nangate45, unsigned)
- Fixed `generate_design.py` to prepend bundled onnxruntime to `LD_LIBRARY_PATH` (avoided rtlgen libonnxruntime error) and to omit MG_CPA.v for pure adders; `run_sweep.py` now reads DEF units to report die_area in µm².
- Generated all adder configs (families Ripple/BrentKung/KoggeStone/Sklansky, widths 4/8/16/32/64, signed+unsigned) via `scripts/generate_adder_configs.py`; added sweep specs under `runs/prefix_adders/sweeps` with `CORE_UTILIZATION=10` to dodge PDN failures on tiny blocks.
- Ran Nangate45 unsigned sweep at 2.5ns/PD=0.55 for all widths/families using `run_sweep.py` (results under `runs/prefix_adders/*/work/ef9c722d`, summary `runs/prefix_adders/nangate45_unsigned_summary.csv`). One earlier PDN-fail attempt at 30% util retained as failed row.
- Observations (Nangate45 unsigned): Kogge-Stone and Sklansky meet 2.5ns through 64b (crit ~0.25ns @64b); Brent-Kung hits ~0.2ns up to 32b but slips to 2.86ns at 64b; Ripple meets 2.5ns through 16b (0.19ns) but misses at 32b (2.52ns) and 64b (4.89ns). Area rises with prefix aggressiveness at 64b: Ripple 11.9k < Brent-Kung 13.2k < Sklansky 15.6k < Kogge-Stone 17.7k; power follows area (0.94–1.12mW at 64b).
- Next: rerun sweeps on asap7/sky130hd (same configs) and add signed summaries; consolidate CSV/plots plus methodology notes in this log or a dedicated prefix-adder doc.

2025-12-16 — Prefix adders on Sky130HD and ASAP7 (unsigned)
- Sky130HD: completed full unsigned sweep (initial 6ns/PD=0.55 plus relaxed 8ns/util=8%/PD=0.5 for stubborn cases). Summary lives at `runs/prefix_adders/sky130hd_unsigned_summary.csv` (25 rows, includes both tags). Kogge-Stone/Sklansky meet 6–8ns across widths; Brent-Kung and Ripple miss at larger widths but are captured for distribution.
- ASAP7: ran baseline and relaxed sweeps; fixed `run_sweep.py` to convert ASAP7 finish-report critical-path values from picoseconds to nanoseconds. Corrected all existing ASAP7 `result.json`/`metrics.csv` entries and regenerated `runs/prefix_adders/asap7_unsigned_summary.csv` (31 rows; mixed baseline/relaxed tags preserved). Typical crit (ns) after conversion: KS64 ~0.396, BK64 ~1.28, Ripple64 ~2.31, Sklansky64 ~0.39.
- Added relaxed sweep specs (`runs/prefix_adders/sweeps/*_relaxed.json`) to ease PDN/route on tiny blocks (util=8%, PD=0.5).
- Outdated `runs/booth_multiplier32s_wrapper` evaluation removed; `runs/README.md` updated to reflect hierarchical `runs/<circuit_type>/<design>/...` layout.

2025-12-17 — 16-bit multiplier PPG+CPA evaluation (Nangate45, unsigned)
- Ran 8 configs (PPG: Normal/Booth4 × CPA: Ripple/KoggeStone/BrentKung/Sklansky) with `CLOCK_PERIOD=2.5`, `CORE_UTILIZATION=10`, `PLACE_DENSITY=0.55`. Outputs under `runs/multipliers/ppg_cpa_16b/`; summary at `runs/multipliers/ppg_cpa_16b/nangate45_summary.csv`.
- Timing: prefix CPA variants landed ~0.216–0.223ns critical path; Brent-Kung/Ripple ~2.31–2.61ns (Booth4 slightly slower on Ripple).
- Area/power: die area ~18.2k–20.1k µm²; total power ~0.00214–0.00387 mW (prefix CPAs highest power).
- Ran signed 16-bit set (Nangate45, same sweep). Summary at `runs/multipliers/ppg_cpa_16b_signed/nangate45_summary.csv`: prefix CPAs ~0.213–0.220ns, ripple ~2.47–2.53ns; die area ~17.6k–20.3k µm²; power ~0.00196–0.00431 mW.
- Ran unsigned 16-bit set on Sky130HD (`CLOCK_PERIOD=6.0`). Summary at `runs/multipliers/ppg_cpa_16b/sky130hd_summary.csv`: prefix ~5.89–6.05ns, Brent-Kung ~9.90–9.96ns, ripple ~11.66–11.88ns; die area ~85.8k–96.7k µm²; power ~0.00445–0.0079 mW.
- Ran unsigned 16-bit set on ASAP7 (`CLOCK_PERIOD=1.0`). Summary at `runs/multipliers/ppg_cpa_16b/asap7_summary.csv`: prefix ~0.63–0.67ns, Brent-Kung ~1.02–1.09ns, ripple ~1.15–1.24ns; die area ~1.22k–1.52k µm²; power ~0.261–0.313 mW.
- Ran signed 16-bit set on Sky130HD (`CLOCK_PERIOD=6.0`). Summary at `runs/multipliers/ppg_cpa_16b_signed/sky130hd_summary.csv`: prefix ~5.79–6.07ns, Brent-Kung ~9.24–9.89ns, ripple ~10.79–11.49ns; die area ~84.5k–92.0k µm²; power ~0.00423–0.0074 mW.
- Ran signed 16-bit set on ASAP7 (`CLOCK_PERIOD=1.0`). Summary at `runs/multipliers/ppg_cpa_16b_signed/asap7_summary.csv`: prefix ~0.63–0.66ns, Brent-Kung ~0.98–1.01ns, ripple ~1.12–1.13ns; die area ~1.22k–1.48k µm²; power ~0.246–0.33 mW.
- Ran 4/8/16/32-bit sweep on Nangate45 (signed+unsigned, Normal/Booth4 × Ripple/KoggeStone/BrentKung/Sklansky) with `CLOCK_PERIOD=2.5`, `CORE_UTILIZATION=10`, `PLACE_DENSITY=0.55`. Results in `runs/multipliers/ppg_cpa_widths_4_32/nangate45_summary.csv` (64 rows).

2025-12-18 — 4/8/16/32-bit multiplier sweeps on Sky130HD + ASAP7
- Completed Sky130HD sweep (signed+unsigned, Normal/Booth4 × Ripple/KoggeStone/BrentKung/Sklansky) with `CLOCK_PERIOD=6.0`, `CORE_UTILIZATION=10`, `PLACE_DENSITY=0.55`. Summary at `runs/multipliers/ppg_cpa_widths_4_32/sky130hd_summary.csv` (64 rows).
- Completed ASAP7 sweep (signed+unsigned, Normal/Booth4 × Ripple/KoggeStone/BrentKung/Sklansky) with `CLOCK_PERIOD=1.0`, `CORE_UTILIZATION=10`, `PLACE_DENSITY=0.55`. Summary at `runs/multipliers/ppg_cpa_widths_4_32/asap7_summary.csv` (64 rows).

2025-12-19 — High-util sweeps, normalized PPA plots, and Booth vs Normal update
- Added high-util sweeps for multipliers (Nangate45 60/50%, Sky130HD 50/40%, ASAP7 60/50%), plus a relaxed 45/40% rerun to capture the missing Nangate45 `mult4u_normal_ripple`. Best-pick CSVs: `best_area_highutil.csv`, `best_delay_highutil.csv`, `best_delay_all.csv`, `best_power_all.csv`.
- Removed redundant pilot runs (`runs/multipliers/ppg_cpa_16b*`), keeping only the width sweep. Updated `runs/README.md` trends to reflect platform-dependent Booth effects (overhead hurts tiny widths; modest gains only on some wider signed cases; ASAP7 usually prefers Normal).
- Generated normalized Booth-vs-Normal plots per platform and signedness, with Booth normalized to the matching Normal+CPA baseline. Script: `analysis/gen_booth_vs_normal_plots.py`; outputs in `analysis/*normalized*`. Updated `notes/booth4_vs_normal/booth_vs_normal_multiplier_comparison.md` to embed these plots, note the 4-bit Sky130HD outlier, and align conclusions with the new data.

2025-12-20 — README sweep (remaining)
- Read `analysis/booth_vs_normal/README.md`: booth-vs-normal delta aggregation sources `runs/campaigns/multipliers/ppg_cpa_widths_4_32/*_summary.csv`; outputs `delta_by_width.csv` + `delta_metrics_by_width.png`.
- Read `runs/README.md`: documents `runs/` layout, contribution flow via `scripts/run_sweep.py` and `scripts/build_runs_index.py`, and summarizes prefix-adder/multiplier trend observations.
- Read `runs/designs/README.md` + `runs/campaigns/README.md`: clarify design artifacts vs campaign configs/sweeps/summaries (keep `work/` scratch and `metrics.csv` append-only).
- Read `json/*` READMEs (vendored nlohmann/json): build/docs/docset tools; gdb pretty-printer, natvis generator, serve_header utility, amalgamate notes, and benchmark report; treat as third-party docs.
- Read `flopoco/README.md` + `flopoco/tools/autotests-html/README.md`: upstream FloPoCo license/overview and CSV→HTML autotest report tool usage.
- Read `pagsuite/README.md`: upstream PAGSuite algorithms/usage/build notes.
- Read `third_party/onnxruntime-linux-x64-1.23.1/README.md`: upstream ONNX Runtime overview and resources.

2026-01-06 — Workflow infrastructure (notes/workflow.md near-term plan)
- Added static web search page at `docs/runs/index.html`: loads `runs/index.csv`, provides filters (circuit_type, platform, design, status), sortable columns (delay/area/power), dark theme.
- Added `docs/metadata_schema.json`: JSON Schema for optional `metadata.json` files under `runs/designs/*/`; required fields: design_id, circuit_type, generator; optional: ops, widths, signedness, ppg, cpa, rtl_source, owner, tags, created_at, notes, references.
- Updated `scripts/validate_runs.py` to validate `metadata.json` files (enum checks, required fields, design_id vs directory name warning).
- Added `.github/workflows/validate-runs.yml`: CI workflow triggers on PRs touching `runs/`; validates schema, regenerates index, fails if index is stale.

2026-03-03 — Two-layer flow clarification + NPU eval pipeline hardening
- Added/extended NPU end-to-end campaign tooling under `npu/eval/`:
  - runner (`run_campaign.py`) with `physical_select` filtering and stable
    `run_id` encoding including `param_hash`,
  - reporting (`report_campaign.py`) with weighted objective ranking and
    Pareto extraction,
  - profile optimizer (`optimize_campaign.py`) for objective-profile sweeps.
- Campaign outputs are now standardized in
  `runs/campaigns/npu/e2e_eval_v0/` (`results.csv`, `summary.csv`,
  `report.md`, `pareto.csv`, `best_point.json`, `objective_sweep.*`,
  per-profile artifacts).
- Improved campaign-run iteration performance:
  - reuse mapper/perf model artifacts by metadata match (default),
  - optional parallel model artifact generation via `--jobs`.
- Added eval regression coverage and CI:
  - `tests/test_eval_campaign_tools.py`,
  - `.github/workflows/npu-eval-tests.yml`.
- Clarified documentation hierarchy and layer split:
  - `docs/structure.md` defines doc-role boundaries and precedence,
  - `docs/two_layer_workflow.md` defines Layer 1 (circuit module physical
    optimization) and Layer 2 (NPU architecture/model optimization) plus
    handoff contract.
- Rewrote top-level `README.md` to present the repository as a two-layer
  generator/optimization system and point to canonical runbooks.

2026-03-03 — Layer1 wrapper-vs-macro contract encoded
- Added `evaluation_scope` to Layer 1 candidate manifests
  (`wrapped_io` / `macro_hardened`) and validation in
  `scripts/validate_runs.py`.
- Seed candidate manifests under `runs/candidates/*/module_candidates.json`
  now explicitly declare current entries as `wrapped_io`.
- Added campaign-side `layer1_modules` contract in `npu/eval`:
  - `manifest`, `variant_ids`, `allow_wrapped_io`
  - validation now rejects wrapped candidates unless override is explicit.
- Updated NPU campaign examples and active campaign to record Layer 1
  candidate references with explicit wrapped override.
- Campaign runner now records Layer 1 candidate provenance in row `notes`
  and logs when wrapped overrides are used.

2026-03-04 — Distributed OpenROAD evaluation queue
- Added a GitHub-exchangeable OpenROAD evaluation queue under
  `runs/eval_queue/openroad/` with:
  - `item.schema.json` (contract),
  - `templates/item_template.json` (authoring template),
  - `queued/` and `evaluated/` state directories.
- Added first queued item for macro-hardening re-evaluation of Layer 1
  Nangate45 seed candidates:
  `runs/eval_queue/openroad/queued/l1_macro_harden_candidates_nangate45_v1.json`.
- Extended `scripts/validate_runs.py` to validate queue items, enforce
  state-directory consistency, unique item IDs, and metrics-row traceability
  for evaluated results.
- Rewrote `notes/evaluation_agent_guidance.md` as evaluator first-read manual
  aligned with queue workflow and validation gates.
- Added explicit queue source-mode contract (`task.source_mode`) and validator
  checks to prevent wrapper hardening commands from being queued in
  `--config` mode.

2026-03-04 — Layer2 campaign handoff update after macro promotion
- Updated `runs/campaigns/npu/e2e_eval_v0/campaign.json` to remove
  `allow_wrapped_io` overrides now that referenced Layer1 candidates are
  `macro_hardened`.
- Updated `npu/eval/examples/minimal_campaign.json` similarly for consistency.
- Added new queued evaluator item:
  `runs/eval_queue/openroad/queued/l2_e2e_macro_hardened_cmp_v1.json`
  to rerun Layer2 campaign/report/objective sweep with the hardened candidates.

2026-03-04 — Sample-aware rerun identity for Layer2 statistics
- Updated `npu/eval/run_campaign.py` so `run_id` remains a stable design-point
  key while each emitted row gets explicit sample identity fields:
  `sample_id`, `batch_id`, `sample_index` (plus optional `--batch_id` CLI).
- Updated result flattening/output behavior:
  - `results.csv` now includes sample columns for rerun traceability.
  - per-row JSON artifact filenames now use `sample_id` when present, avoiding
    overwrite across repeated samples of the same `run_id`.
- Updated reporting semantics in `npu/eval/report_campaign.py`:
  - aggregate statistics naturally include multiple samples per `run_id`,
  - duplicate `sample_id` rows are deduplicated (latest row wins),
  - report header records `duplicate_sample_rows_dropped`.
- Updated validation/contracts/docs/tests for the new model:
  - `npu/eval/validate.py` and `npu/eval/result_row.schema.json`,
  - `npu/eval/contract.md` and `npu/eval/README.md`,
  - regression coverage in `tests/test_eval_campaign_tools.py`.
- Rationale: statistical reruns are valid and should be retained, but they
  should not be represented as duplicate `run_id` identities.

2026-03-05 — Phase-5 bootstrap: model-set revision + physical-reuse campaign scaffold
- Added new versioned model set under `runs/models/mlp_smoke_v1/`:
  - `manifest.json` with SHA256-pinned ONNX entries,
  - `README.md` with regeneration/hash update procedure,
  - copied smoke ONNX binaries (`mlp1.onnx`, `mlp2.onnx`) as immutable set assets.
- Added new campaign scaffold:
  - `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign.json`
  - includes `model_set_id=mlp_smoke_v1` and
    `physical_source_campaign=runs/campaigns/npu/e2e_eval_v0/campaign.json`.
  - output paths isolated under the new campaign directory.
- Added campaign runbook files:
  - `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/README.md`
  - `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/objective_profiles.json`
- Updated docs for discoverability and policy:
  - `runs/models/README.md` (model-set revision policy + current sets),
  - `npu/eval/README.md` (reuse-campaign validation example and
    `physical_source_campaign` note).
- Executed the new reuse campaign locally (no `--run_physical`) to get baseline
  model-level rankings:
  - generated 40 result rows in
    `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/results.csv`.
  - all objective profiles (`balanced/latency/energy/runtime_bal/ppa`) selected
    `arch_id=fp16_nm1`, `macro_mode=flat_nomacro` as current best.
- Added focused evaluator queue item for OpenROAD rerun:
  - `runs/eval_queue/openroad/queued/l2_e2e_mlp_smoke_v1_focus_flat_v1.json`
  - requests flat-mode-only (`--modes flat_nomacro`) physical reruns at
    higher repeat count (`--repeat 10`) with explicit batch identity
    `l2_e2e_mlp_smoke_v1_focus_flat_v1_rerun1`.
- Queue handoff prepared for evaluator: refreshed metadata on
  `l2_e2e_mlp_smoke_v1_focus_flat_v1` (created_utc/requested_by) and kept item
  in `runs/eval_queue/openroad/queued/` for immediate HPC pickup.

2026-03-05 — Phase-5 continuation: `mlp_smoke_v2` scaffold + baseline run
- Restored queue scaffold tracking by adding:
  - `runs/eval_queue/openroad/queued/.gitkeep`
  so the queued state directory persists in git when empty.
- Added next model-set revision scaffold under `runs/models/mlp_smoke_v2/`:
  - `manifest.json` with SHA256-pinned ONNX entries,
  - `README.md` with regeneration/hash update steps,
  - copied `mlp1.onnx` / `mlp2.onnx` from `mlp_smoke_v1` as initial placeholders.
- Added new reuse campaign scaffold:
  - `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/campaign.json`
  - `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/README.md`
  - `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/objective_profiles.json`
  - uses `model_set_id=mlp_smoke_v2` and
    `physical_source_campaign=runs/campaigns/npu/e2e_eval_v0/campaign.json`.
- Executed local Layer2 baseline run (no `--run_physical`) and generated
  reporting artifacts:
  - `results.csv`, `summary.csv`, `report.md`, `pareto.csv`, `best_point.json`
  - `objective_sweep.csv`/`objective_sweep.md`
  - per-profile outputs under `objective_profiles/*`
  - result-row JSON artifacts under `artifacts/result_rows/`
- Outcome: all objective profiles again selected
  `arch_id=fp16_nm1`, `macro_mode=flat_nomacro` as best for this smoke set.

2026-03-05 — Phase-5 continuation: replace `mlp_smoke_v2` placeholders with scaled models
- Extended lite ONNX MLP generator presets:
  - `npu/mapper/onnx_lite.py`: added `mlp3`, `mlp4`
  - `npu/mapper/examples/gen_mlp_onnx_lite.py`: exposed new presets in CLI
- Tuned `mlp4` to fit current `minimal.yml` SRAM constraints:
  - shape set to `b=64, in=1024, hidden=2048, out=1020`
  - rationale: `out=1024` exceeded `weight_sram` by a small margin and failed
    schedule generation (`out of space in region weight_sram`).
- Regenerated `runs/models/mlp_smoke_v2/` ONNX files:
  - `mlp1.onnx` from `mlp3`
  - `mlp2.onnx` from adjusted `mlp4`
  - updated `manifest.json` hashes and model notes; updated model-set docs.
- Re-ran `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/` from clean outputs
  (no `--run_physical`), then regenerated report + objective profiles.
- Outcome: with scaled models, profile winners remain
  `arch_id=fp16_nm1`, `macro_mode=flat_nomacro`; latency/energy magnitudes
  increased as expected versus the previous small-smoke placeholders.

2026-03-05 — Large-model mapping note and next-step definition
- Noted explicit blocker: to evaluate larger MLP/ONNX models, mapper must
  support model split/tiling instead of requiring monolithic SRAM fit.
- Added mapper split plan document:
  - `npu/docs/mapper_split_plan.md`
  - defines phase-1 policy: N-axis chunking for oversize GEMM stage.
- Synced requirement across canonical docs:
  - `npu/mapper/mapping_contract.md`
  - `npu/mapper/README.md`
  - `npu/docs/workflow.md`
  - `npu/docs/eval_flow_plan.md`
  - `npu/docs/index.md`
- Next implementation step:
  - add phase-1 chunked lowering in `npu/mapper/onnx_to_schedule.py`
  - add regression coverage for prior SRAM-overflow case.

2026-03-05 — Mapper phase-1 split implementation (GEMM2 output chunking)
- Implemented phase-1 large-model lowering in:
  - `npu/mapper/onnx_to_schedule.py`
- Key behavior changes:
  - weight SRAM is now reused between GEMM1 and GEMM2 staging instead of
    monolithic `W1+W2` co-allocation,
  - GEMM2 supports automatic output-channel chunking when `W2+b2` exceeds
    available weight SRAM,
  - chunked schedule emits per-chunk DMA/GEMM/DMA sequence with deterministic
    dependencies and final event on last output DMA.
- Added schedule metadata:
  - `mapper_notes.gemm2_out_chunks`
  - `mapper_notes.gemm2_split_enabled`
  - `mapper_notes.gemm2_weight_layout=packed_by_output_chunk`
- Validation executed:
  - `make -f npu/mapper/Makefile validate example-bin onnx-mlp1 onnx-mlp2`
  - manual oversized ONNX (`b=32,in=512,hidden=2048,out=4096`) now lowers
    successfully with split plan `[2047, 2047, 2]`, and descriptor emission
    succeeds.

2026-03-05 — Mapper split regression test + CI wiring
- Added new regression test:
  - `tests/test_mapper_split.py`
  - covers both:
    - fit case (no split expected),
    - oversized case (split expected, chunk/dependency/event checks, descriptor
      emission success).
- Wired test into CI workflow:
  - `.github/workflows/npu-golden-sim.yml`
  - adds explicit step: `python3 tests/test_mapper_split.py`
  - includes workflow path trigger on `tests/test_mapper_split.py`.
- Local validation:
  - `python3 tests/test_mapper_split.py` passed.

2026-03-05 — Split-path integration in Layer2 campaign (`mlp_smoke_v2`)
- Updated `mlp4` lite preset in `npu/mapper/onnx_lite.py` to intentionally
  oversized dimensions for monolithic mapping:
  - `b=64, in=1024, hidden=2048, out=4096`
- Regenerated model-set artifacts for `runs/models/mlp_smoke_v2/`:
  - updated `mlp2.onnx` hash and notes in `manifest.json`
  - updated `README.md` to document split-path intent.
- Re-ran `runs/campaigns/npu/e2e_eval_mlp_smoke_v2_reuse/` from clean outputs
  and regenerated reporting/objective artifacts.
- Confirmation of split-path activation in campaign artifacts:
  - `artifacts/mapper/mlp2/descriptors.bin` expanded from 23 to 51 descriptors,
  - `artifacts/mapper/mlp2/schedule.yml` includes:
    - `mapper_notes.gemm2_split_enabled=true`
    - `mapper_notes.gemm2_out_chunks=[2047, 2047, 2]`
    - completion event on `dma_y_c2`.
- Campaign outcome remains stable on ranking:
  - best profile point still `fp16_nm1 + flat_nomacro`,
  - aggregate latency/energy increased versus smaller model set as expected.

2026-03-05 — Campaign row notes: mapper split metadata
- Updated `npu/eval/run_campaign.py` to attach mapper split provenance in each
  emitted row `notes` by parsing `artifacts/mapper/*/schedule.yml`:
  - `mapper_split_enabled=<0|1>`
  - `mapper_split_chunk_count=<N>`
  - `mapper_split_chunks=<comma-separated N list>`
- Notes are emitted for both split and non-split schedules, so CSV filtering
  can directly separate split vs baseline runs.
- Added parser regression test:
  - `tests/test_run_campaign_mapper_notes.py`
  - covers explicit `mapper_notes` path and fallback-from-ops path.
- Wired into CI:
  - `.github/workflows/npu-eval-tests.yml` now runs
    `tests/test_run_campaign_mapper_notes.py` in addition to existing eval tests.
- Documentation updated:
  - `npu/eval/README.md`
  - `npu/eval/contract.md`

# NPU OpenROAD Synthesis Plan

## Purpose
This plan outlines how to integrate NVDLA hardware references into RTLGen's
OpenROAD evaluation flow for block-level NPU macros.

## Goals
- Reuse NVDLA `hw/syn` scripts as a baseline for constraints and targets.
- Provide RTLGen wrappers that emit consistent `verilog/` outputs for OpenROAD.
- Record results in `runs/designs/` using the same append-only `metrics.csv`.

## Reference inputs
- NVDLA HW repository: `npu/nvdla/hw`
  - `syn/` contains example synthesis scripts and constraints.
  - `spec/` contains configuration settings and performance assumptions.

## Proposed wrapper flow
1) Generate RTL (RTLGen NPU generator) for a target macro:
   - compute tile
   - SRAM wrapper
   - DMA engine
2) Emit a design directory under `runs/designs/npu/<design>/` with:
   - `verilog/`
   - `config.json` or `arch.yml`
   - `README.md` describing the macro and config hash
3) Provide a sweep definition in `runs/campaigns/npu/<campaign>/sweeps/`.
4) Invoke OpenROAD via `npu/synth/run_block_sweep.py` (block-level wrapper).

## Constraint alignment
- Translate NVDLA `syn` SDC parameters into OpenROAD constraints:
  - clock period / uncertainty
  - IO delays
  - load assumptions
- Capture default floorplan hints in `npu/synth/floorplan.md`.

## Output expectations
- Timing, area, and power in `metrics.csv`.
- Config hashes recorded per run.
- Any NVDLA-specific knobs reflected in `params_json`.

## Near-term tasks
- Inventory key NVDLA `syn` scripts and extract common SDC knobs.
- Draft a minimal NPU macro wrapper config in `runs/campaigns/npu/`.
- Validate that `npu/synth/run_block_sweep.py` can target NPU macro designs
  with custom SDC and floorplan constraints.
- Add a C++ RTLGen MAC block target (`operations[].type="mac"`,
  `accumulation_mode="pp_row_feedback"`) for multiplier/MAC PPA exploration.

## Status
- RTL shell and DMA stub are available.
- Hierarchical compute-macro pre-synthesis is available:
  - `npu/synth/pre_synth_compute.py`
  - emits per-macro `macro_manifest.json` consumable by
    `npu/synth/run_block_sweep.py --macro_manifest ...`
  - integrates hardened LEF/LIB (+ optional GDS) through
    `ADDITIONAL_LEFS`/`ADDITIONAL_LIBS` and `SYNTH_BLACKBOXES`
  - emits blackbox stub Verilog and `run_block_sweep.py` auto-injects it
    for Yosys hierarchy resolution
  - includes a two-pass synth workaround (synth with `ADDITIONAL_LIBS=`,
    then continue with `SYNTH_NETLIST_FILES=...`) to avoid macro-lib ABC
    crashes in hierarchical top-level runs
- FP16 backend sweep harness is available:
  - `npu/synth/run_fp16_backend_sweep.py`
  - `npu/synth/fp16_backend_sweep_nangate45.json`
  - `runs/designs/npu_blocks/npu_fp16_builtin_l1`
  - `runs/designs/npu_blocks/npu_fp16_cpp_l1`
- FP16 backend sweep executed at `make_target=3_5_place_dp` (Nangate45):
  - report: `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`
  - measured `builtin_raw16` and `cpp_ieee` successfully
  - latest metrics:
    - `builtin_raw16`: `critical_path_ns=5.4414`, `die_area=2250000`, `total_power_mw=0.2014`
    - `cpp_ieee`: `critical_path_ns=5.6592`, `die_area=2250000`, `total_power_mw=0.1976`
  - default recommendation is `cpp_ieee` (builtin excluded from default lock
    because it is a non-IEEE placeholder backend)
- FP16 backend finish-level sign-off completed at `make_target=finish`:
  - `builtin_raw16`: `critical_path_ns=5.4287`, `die_area=2250000`, `total_power_mw=0.233`
  - `cpp_ieee`: `critical_path_ns=5.6462`, `die_area=2250000`, `total_power_mw=0.229`
  - recommendation remains `cpp_ieee` among default-eligible backends.

## Hierarchical macro flow (quick start)
1) Harden a C++ RTLGen macro to abstract views:
```sh
python3 npu/synth/pre_synth_compute.py \
  --config examples/config_mac_pp_feedback.json \
  --platform nangate45 \
  --rtlgen_bin build/rtlgen \
  --clock_port ""
```
For generator-emitted RTL modules (for example `gemm_compute_array` inside
`npu_top.v`), harden directly from an existing RTL directory:
```sh
python3 npu/synth/pre_synth_compute.py \
  --src_verilog_dir runs/designs/npu_blocks/npu_fp16_cpp_hiercmp/verilog \
  --src_module_file npu_top.v \
  --module gemm_compute_array \
  --manifest_param compute.gemm.mac_type=fp16 \
  --manifest_param compute.gemm.mac_source=rtlgen_cpp \
  --manifest_param compute.gemm.num_modules=2 \
  --manifest_param compute.gemm.lanes=1 \
  --platform nangate45 \
  --clock_port ""
```
2) Use emitted manifest for top-level sweep:
```sh
python3 npu/synth/run_block_sweep.py \
  --design_dir runs/designs/npu_blocks/npu_fp16_cpp_l1 \
  --platform nangate45 \
  --top npu_fp16_cpp_l1 \
  --sweep npu/synth/fp16_backend_sweep_nangate45.json \
  --macro_manifest runs/designs/npu_macros/<macro_id>/macro_manifest.json
```
3) For multiple hardened variants, use a macro library (example:
`npu/synth/macro_library_example.json`) and selector context from RTL config:
```sh
python3 npu/synth/run_block_sweep.py \
  --design_dir runs/designs/npu_blocks/npu_fp16_cpp_hiercmp \
  --platform nangate45 \
  --top npu_top \
  --sweep npu/synth/fp16_backend_sweep_nangate45.json \
  --macro_library npu/synth/macro_library_example.json \
  --macro_select_json npu/rtlgen/examples/minimal_fp16_cpp.json \
  --macro_required
```
4) To compare flattened vs hierarchical-hardmacro in one sweep run, set
`mode_compare` in the sweep JSON and run once:
```json
{
  "tag_prefix": "npu_fp16_hiercmp",
  "mode_compare": true,
  "flow_params": {
    "CLOCK_PERIOD": [10.0],
    "DIE_AREA": ["0 0 1500 1500"],
    "CORE_AREA": ["50 50 1450 1450"],
    "PLACE_DENSITY": [0.40]
  }
}
```
`mode_compare: true` runs default `flat_nomacro` and `hier_macro` modes and
emits one markdown comparison report per sweep point under
`runs/designs/<type>/<design>/comparisons/`.
The report now includes:
- per-mode summary statistics (mean/stddev) for timing, area, power, and
  elapsed time
- per-run raw rows (including repeat index)
- `metrics.csv` rows now record run-local provenance fields including
  `work_result_json`, `synth_script_path`, and `synth_script_sha1` so
  hierarchical synth behavior can be reproduced exactly.

To reduce run-to-run jitter, repeat each sweep point/mode multiple times:
```json
{
  "mode_compare": {
    "enabled": true,
    "repeat": 5,
    "modes": [
      { "name": "flat_nomacro", "use_macro": false },
      { "name": "hier_macro", "use_macro": true }
    ]
  }
}
```
You can also override repeats from CLI:
```sh
python3 npu/synth/run_block_sweep.py ... --repeat 5
```
5) For fp16 backend comparisons, pass through with:
```sh
python3 npu/synth/run_fp16_backend_sweep.py \
  --platform nangate45 \
  --sweep npu/synth/fp16_backend_sweep_nangate45.json \
  --macro_library npu/synth/macro_library_example.json \
  --macro_required
```
Note: top-level sweeps now fail fast if a macro LEF outline is larger than the
requested `CORE_AREA`; either re-harden with smaller macro die/core area or
increase top-level floorplan dimensions.

## Next steps
- Add deterministic macro-placement runbooks (`macro_placement.tcl`) for compute
  + SRAM + DMA compositions.
- Extend macro hardening presets beyond `mac` to adder/multiplier variants with
  stable naming and cache-key policy.
- Keep fp16 backend finish-level sweep as a regression gate when generator
  defaults or fp16 datapath semantics change.

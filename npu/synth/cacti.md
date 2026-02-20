# CACTI SRAM Estimation

## Purpose
This document describes the SRAM pre-synthesis stage in the NPU workflow.
CACTI is a fallback estimator when a real PDK-specific SRAM generator is not
available for the selected run.

## Workflow summary
- SRAM instances are defined in architecture YAML:
  - v0.1: `sram.instances`
  - v0.2-draft: `memory.instances` (+ `platform.target_pdk`, `platform.tech_node_nm`)
- `npu/synth/pre_synth_memory.py` is the pipeline entrypoint:
  - tries external SRAM generator first (when configured),
  - falls back to `npu/synth/sram_ppa.py` (CACTI).
- Canonical pre-synth output is:
  - `runs/designs/sram/<id>/sram_metrics.json`
  - `runs/designs/sram/<id>/sram_metrics.pre_synth.json`
  - `runs/designs/sram/<id>/pre_synth_memory.json`
- CACTI input templates live in `npu/synth/cacti_sram.cfg.in`.
- For sky130hd (and other PDKs with real macro compilers), CACTI should be
  treated as fallback/interim estimation.

## Pre-synth stage modes
- `auto` (default): use memgen if configured; otherwise CACTI fallback.
- `memgen_only`: require memgen command success.
- `cacti_only`: force CACTI path.

`pre_synth_memory.py` memgen command placeholders:
- `{arch}` `{id}` `{out_root}` `{out_dir}` `{pre_dir}` `{memgen_dir}` `{pdk}`

## Tech node handling (>90nm)
CACTI (HP version) only supports feature sizes up to 90nm. For any SRAM instance
with `tech_node_nm > 90`, the flow:
1) Runs CACTI at 90nm.
2) Scales the outputs back to the requested node.

Scaling rules (coarse, first-order):
- **Area**: scale by (N/90)^2
- **Energy**: scale by (N/90)^2
- **Access time**: scale by (N/90)

The `sram_metrics.json` includes:
- `cacti_node_nm` (the node used for CACTI)
- `scaled_from_nm` (the requested node)
- `scale_factor` (N/90)

## PDK mapping
If `tech_node_nm` is not provided, `sram_ppa.py` maps `pdk` values to nodes:
- `sky130` → 130
- `nangate45` → 45
- `asap7` → 7

## Known limitations
- CACTI is an estimator; it does not replace macro compilers.
- For sky130hd, the intended path is to generate real SRAM macros and extract
  PPA from layout. CACTI should be treated as an interim estimate only.

## Usage
Run pre-synth stage (recommended):
```sh
python3 npu/synth/pre_synth_memory.py npu/arch/examples/minimal.yml --id minimal
```

Run pre-synth with explicit memgen command:
```sh
python3 npu/synth/pre_synth_memory.py npu/arch/examples/minimal.yml --id minimal \
  --mode auto \
  --memgen-cmd 'python3 tools/memgen/run.py --arch {arch} --out {memgen_dir} --pdk {pdk}' \
  --memgen-metrics '{memgen_dir}/sram_metrics.json'
```

Run CACTI directly:
```sh
python3 npu/synth/sram_ppa.py npu/arch/examples/minimal.yml --id minimal --cacti-bin /workspaces/RTLGen/third_party/cacti/cacti
```

Or via pipeline:
```sh
npu/run_pipeline.sh npu/arch/examples/minimal.yml --sram-id minimal
```

# CACTI SRAM Estimation

## Purpose
This document describes how CACTI is used to estimate SRAM PPA metrics in the
NPU workflow, especially when the target PDK does not have a macro generator.

## Workflow summary
- SRAM instances are defined in `npu/arch/*.yml` under `sram.instances`.
- `npu/synth/sram_ppa.py` runs CACTI and writes
  `runs/designs/sram/<id>/sram_metrics.json`.
- CACTI input templates live in `npu/synth/cacti_sram.cfg.in`.
- For sky130hd (and other PDKs with real macros), CACTI estimates are placeholders
  until macro generation and extraction are wired in.

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
Run directly:
```sh
python3 npu/synth/sram_ppa.py npu/arch/examples/minimal.yml --id minimal --cacti-bin /workspaces/RTLGen/cacti/cacti
```

Or via pipeline:
```sh
npu/run_pipeline.sh npu/arch/examples/minimal.yml --sram-id minimal
```

# NPU Mapping Contract (Draft v0.1)

## Purpose
Define the **end-to-end contract** between model/graph inputs, the mapper,
and downstream consumers (RTL sim, perf sim, and synthesis/analysis).
This is higher-level than `ir.md` and is intended to specify what the mapper
must accept and what artifacts it must emit.

## Scope (v0.1)
- Minimal, deterministic inputs for mapping and scheduling.
- Explicit target constraints (memory sizes, DMA bandwidth, compute shape).
- Output artifacts that feed RTL/perf simulations and reporting.

## 1) Input Contract
Top-level fields (YAML/JSON):
```yaml
version: 0.1
arch: npu/arch/<arch>.yml
model:
  name: resnet50
  graph: path/to/graph.onnx
  inputs:
    - name: input0
      shape: [1, 3, 224, 224]
      dtype: fp16
targets:
  memory_spaces:
    - name: dram
      base_addr: 0x0000_0000
      bytes: 0x2000_0000
    - name: sram0
      base_addr: 0x8000_0000
      bytes: 0x0010_0000
  dma:
    max_read_bw_gbps: 16.0
    max_write_bw_gbps: 16.0
  compute:
    gemm:
      m_tile: 64
      n_tile: 64
      k_tile: 32
constraints:
  max_cq_depth: 1024
  alignment_bytes: 32
```

Notes:
- `arch` is authoritative for hardware capabilities.
- `targets` can override or refine architecture defaults.

## 2) Mapper Responsibilities
- Legalize operations against `arch` and `targets`.
- Assign buffers to memory spaces with alignment and size constraints.
- Emit a schedule with explicit ordering (events) and placement info.

## 3) Output Artifacts
The mapper must emit:
1) **Schedule IR** (`*.yml`) using `npu/mapper/ir.md`.
2) **Descriptor stream** (`*.bin`) for RTL sim (`npu/sim/rtl/`).
3) **Descriptor YAML** (`*.desc.yml`) for debugging / auditability.
4) **Perf inputs** (`*.perf.json`) for `npu/sim/perf/`.
5) **Report** (`*.report.json`) with summary metrics and legality checks.

## 4) Mapping Path (High Level)
1) Load `arch` + `model` + `targets`.
2) Lower graph to op list with tensor metadata.
3) Tile + schedule ops against constraints.
4) Allocate buffers and assign addresses.
5) Emit schedule IR + descriptors + perf inputs.

## 5) Compatibility with v0.1 IR
- Each scheduled op maps 1:1 to a descriptor.
- Dependencies are made explicit with `event_signal`/`event_wait`.
- Buffers map to absolute addresses in `buffers[]`.

## Next steps
- Define a minimal JSON schema and validate the input contract in
  `npu/mapper/validate.py`.
- Add a tiny golden workload that exercises the full mapping path.

# NPU RTLGen Config (v0.1 Draft)

## Purpose
This file defines the minimal configuration schema for the NPU RTL generator
used in RTL simulation bring-up. The goal is a **small, stable config** that
can later be extended without breaking v0.1.

## Current status
- Implemented in `npu/rtlgen/gen.py` with RTL + AXI-Lite wrapper outputs.

## Inputs / outputs
- Input: JSON config (this schema).
- Outputs: `top.v`, optional `top_axi.v` and `axi_lite_mmio_bridge.sv`.

## Top-level fields
```json
{
  "version": "0.1",
  "top_name": "npu_top",
  "mmio_addr_width": 12,
  "data_width": 32,
  "dma_addr_width": 64,
  "dma_data_width": 256,
  "axi_addr_width": 64,
  "axi_data_width": 256,
  "axi_id_width": 4,
  "sram_instances": [
    {
      "name": "activation_sram",
      "depth": 16384,
      "width": 256,
      "banks": 8,
      "read_latency": 1,
      "byte_en": true,
      "port": "1r1w",
      "pdk": "sky130",
      "tech_node_nm": 130,
      "base_addr": "0x80000000",
      "alignment_bytes": 64
    }
  ],
  "queue_depth": 16,
  "enable_irq": true,
  "enable_dma_ports": true,
  "enable_cq_mem_ports": true,
  "enable_axi_ports": true,
  "enable_axi_lite_wrapper": false,
  "compute": {
    "enabled": true,
    "gemm": {
      "mac_type": "int8",
      "mac_source": "builtin_int8_dot",
      "lanes": 8,
      "accum_width": 32,
      "pipeline": 1,
      "rtlgen_cpp": {
        "binary_path": "build/rtlgen",
        "module_name": "gemm_mac_int8_pp",
        "ppg_algorithm": "Booth4",
        "compressor_structure": "AdderTree",
        "compressor_library": "fa_ha",
        "compressor_assignment": "legacy_fa_ha",
        "cpa_structure": "BrentKung"
      }
    },
    "vec": {
      "lanes": 8,
      "ops": ["add", "mul", "relu"],
      "activation_source": "builtin",
      "rtlgen_cpp": {
        "binary_path": "build/rtlgen",
        "module_prefix": "vec_act"
      }
    }
  }
}
```

## Field definitions
- `version` (string): config version, must be `"0.1"`.
- `top_name` (string): name of top module to emit.
- `mmio_addr_width` (int): address width for MMIO (bytes).
- `data_width` (int): data width for MMIO and control (bits).
- `dma_addr_width` (int): DMA address width (bits).
- `dma_data_width` (int): DMA data width (bits).
- `axi_addr_width` (int): AXI address width (bits).
- `axi_data_width` (int): AXI data width (bits).
- `axi_id_width` (int): AXI ID width (bits).
- `sram_instances` (list): optional SRAM instances for shell integration and PPA estimation.
  - Each instance should include `name`, `depth`, `width`, `banks`, `read_latency`,
    `byte_en`, `port` (1r1w), and `pdk` or `tech_node_nm`.
  - Optional fields: `base_addr` (hex string or int) and `alignment_bytes` (int).
- `queue_depth` (int): number of 32B descriptors in the command queue.
- `enable_irq` (bool): include IRQ output.
- `enable_dma_ports` (bool): include a stub DMA/memory interface.
- `enable_cq_mem_ports` (bool): include a command queue memory read port.
- `enable_axi_ports` (bool): include AXI4-like memory interface ports (stub).
- `enable_axi_lite_wrapper` (bool): emit an AXI-Lite wrapper module for MMIO.
- `compute` (object, optional): Phase 1 compute generation controls.
  - `compute.enabled` (bool): enable generated GEMM compute datapath hooks.
- `compute.gemm.mac_type` (string): GEMM MAC operand type.
  - `int8`: 8-bit signed lanes (`lanes` in `[1,8]`)
  - `int16`: 16-bit signed lanes (`lanes` in `[1,4]`)
  - `fp16`: 16-bit lanes (default backend is C++ IEEE-half `fp_mac`)
- `compute.gemm.mac_source` (string): GEMM MAC backend selection.
  - `builtin_int8_dot` (or `builtin`): generated `gemm_mac_int8` lane dot-product module.
  - `builtin_int16_dot` (or `builtin`): generated `gemm_mac_int16` lane dot-product module.
  - `builtin_fp16_dot` (or `builtin`): generated `gemm_mac_fp16` raw16 placeholder lane dot-product module (explicit baseline only).
  - `rtlgen_cpp`: uses C++ `build/rtlgen` MAC generator and embeds the generated Verilog in `top.v`.
  - Default behavior:
    - `mac_type=int8` -> `builtin_int8_dot`
    - `mac_type=int16` -> `builtin_int16_dot`
    - `mac_type=fp16` -> `rtlgen_cpp` (default fp16 backend lock)
- `compute.gemm.lanes` (int): number of MAC lanes (depends on `mac_type`).
- `compute.gemm.accum_width` (int): signed accumulator width (16..64).
- `compute.gemm.pipeline` (int): reserved pipeline knob (must be >=1).
- `compute.gemm.fp16` (object, optional): fp16 numeric policy lock (used when `mac_type=fp16`).
  - `semantics` (string): one of:
    - `ieee_half` (default when `mac_source=rtlgen_cpp` or `mac_source` is omitted for fp16)
    - `raw16_placeholder` (explicit fallback for builtin fp16 placeholder backend)
  - `accumulation` (string): accumulation mode (`int32`, `fp32`, `fp16`).
    - default: `fp16` for fp16 `rtlgen_cpp`, `int32` for builtin fp16 placeholder.
  - `rounding` (string): rounding mode policy (`rne`).
  - `subnormals` (string): subnormal policy (`preserve` or `flush`).
- `compute.gemm.rtlgen_cpp` (object, optional): options for `mac_source=rtlgen_cpp`.
  - `binary_path` (string): path to C++ RTLGen binary (default `build/rtlgen`).
  - `module_name` (string): generated MAC module name.
  - `ppg_algorithm`, `compressor_structure`, `compressor_library`,
    `compressor_assignment`, `cpa_structure`: forwarded to C++ MAC config.
- `compute.vec.ops` (list[string]): declared vector ops for staged bring-up.
- `compute.vec.lanes` (int, optional): vector lane count for VEC unit (`1..8`, default `8`).
- `compute.vec.activation_source` (string): activation backend selector for Phase 2.
  - `builtin`: keep activation logic in NPU generator path.
  - `rtlgen_cpp`: import activation modules generated by C++ RTLGen (`relu`, `gelu`,
    `softmax`, `layernorm`, `drelu`, `dgelu`, `dsoftmax`, `dlayernorm`).
- `compute.vec.rtlgen_cpp` (object, optional): options for `activation_source=rtlgen_cpp`.
  - `binary_path` (string): path to C++ RTLGen binary (default `build/rtlgen`).
  - `module_prefix` (string): prefix used for generated activation module names.
  - `activation_operand_kind` (string, optional): activation operand mode (`int8` default, or `fp16`).
  - `activation_fp_total_width` (int, optional): fp operand total width when `activation_operand_kind=fp16` (currently `16`).
  - `activation_fp_mantissa_width` (int, optional): fp operand mantissa width when `activation_operand_kind=fp16` (currently `10`).

## Notes
- The initial RTL is a stub for **simulation harnessing** only.
- Compute and DMA engines are placeholders; the interface and queues are the
  focus of v0.1.
- SRAM instances are emitted as standalone 1R1W modules for simulation and
  blackbox/synth integration (wiring TBD).
- Phase 1 adds an int8 MAC primitive (`gemm_mac_int8`) and uses it in GEMM
  slot execution while preserving existing descriptor timing behavior.
- Phase 3 adds an int16 MAC primitive (`gemm_mac_int16`) under
  `compute.gemm.mac_type=int16`.
- Phase 3 also adds an fp16 selector (`compute.gemm.mac_type=fp16`) as a
  C++ IEEE-half backend by default (`compute.gemm.mac_source=rtlgen_cpp`).
- Builtin fp16 remains available as an explicit raw16 placeholder baseline:
  - `compute.gemm.mac_source=builtin_fp16_dot`
  - `compute.gemm.fp16.semantics=raw16_placeholder`
  - `compute.gemm.fp16.accumulation=int32`
- `mac_source=rtlgen_cpp` scalar MAC constraints:
  - `mac_type=int8`: `lanes=1`, `accum_width=16`
  - `mac_type=fp16`: `lanes=1`, `accum_width=16`,
    `fp16.semantics=ieee_half`, `fp16.accumulation=fp16`,
    `fp16.rounding=rne`, `fp16.subnormals=preserve`
- `activation_source=rtlgen_cpp` emits scalar activation modules for
  `relu`, `gelu`, `softmax`, `layernorm`, `drelu`, `dgelu`, `dsoftmax`,
  and `dlayernorm`.
- When `activation_operand_kind=fp16`, generated modules use C++ RTLGen fp
  activation format (FloPoCo-style `total_width+2` bits). They are wired into
  fp16 VEC activation routing when `compute.vec.fp16_arith_source=rtlgen_cpp`,
  and can also be evaluated standalone.
- VEC op encoding uses the descriptor `flags` byte as:
  - high nibble `[7:4]`: dtype code
  - low nibble `[3:0]`: op code
    - `0:relu`, `1:add`, `2:mul`, `3:gelu`, `4:softmax`, `5:layernorm`,
      `6:drelu`, `7:dgelu`, `8:dsoftmax`, `9:dlayernorm`
- When `enable_axi_lite_wrapper` is true, the generator emits:
  - `top_axi.v` (AXI-Lite top wrapper)
  - `axi_lite_mmio_bridge.sv` (bridge module)

## Next steps
- Extend config fields to cover compute tiles and DMA parameters.
- Add additional MAC types (`int16`, `fp16`) behind config switches.
- Keep compatibility with `compute.enabled=false` for stub-only validation
  flows during migration.
- See `npu/docs/sim_dev_plan.md` section "A.1) Compute Bring-up Plan" for
  phased implementation and validation gates.

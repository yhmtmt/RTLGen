# Configuration File

RTLGen consumes a JSON description of the operands that enter the design and the arithmetic operations that must be generated. Starting with schema version **1.1**, one configuration file can describe multiple operations (e.g., an adder and an MCM block) while keeping the legacy single-operation layout fully compatible.

## Layout Overview

Top-level fields:

- `version` (optional): `"1.1"` enables the multi-operation layout. Missing or `"1.0"` falls back to the legacy behavior.
- `operand`: legacy default operand definition. It is still accepted for backward compatibility.
- `operands` (optional): array of operand descriptions. Each description must provide the uniform fields `name`, `dimensions`, `bit_width`, and `signed`.
  - `name`: base identifier for the operand (e.g., `"sample"`). Every lane is referenced as `<name>_<index>` and indices are generated automatically based on `dimensions`.
  - `dimensions`: positive integer. `1` represents a scalar, larger values describe vectors (e.g., `4` generates `sample_0` … `sample_3`).
  - `bit_width`: width of each lane.
  - `signed`: signedness of each lane.
  - `kind` (optional): `"int"` (default) or `"fp"`. For floating point, supply `fp_format` with `total_width` and `mantissa_width` (exponent is derived as `total_width - mantissa_width - 1`). `bit_width` is auto-filled from `total_width`.
- `operations` (optional): array of operation objects. Each object declares a `type`, `module_name`, the operand(s) it uses, and the type-specific options.

### Legacy Layout (still valid)

```json
{
    "operand": {
        "bit_width": 16,
        "signed": true
    },
    "multiplier": {
        "module_name": "booth_multiplier32s",
        "ppg_algorithm": "Booth4",
        "compressor_structure": "AdderTree",
        "cpa_structure": "KoggeStone",
        "pipeline_depth": 1
    }
}
```

### Operations Array Layout

```json
{
    "version": "1.1",
    "operands": [
        { "name": "sample", "dimensions": 1, "bit_width": 16, "signed": true }
    ],
    "operations": [
        {
            "type": "multiplier",
            "module_name": "booth_multiplier32s",
            "operand": "sample",
            "options": {
                "ppg_algorithm": "Booth4",
                "compressor_structure": "AdderTree",
                "cpa_structure": "KoggeStone",
                "pipeline_depth": 1
            }
        }
    ]
}
```

Every new operation described below can be added either as a dedicated entry inside `operations` (recommended) or by using the legacy top-level keys (`adder`, `multiplier`, etc.).

## Adder Configuration

An adder entry may either reuse the legacy object (`"adder": { ... }`) or be written inside the `operations` array with `"type": "adder"`. Reference the operand you want via the `operand` field (e.g., `"operand": "sample"`) so the generator can extract its width and signedness, then select the CPA structure.

Supported `cpa_structure` values:

- `Ripple` – Ripple Carry Adder
- `KoggeStone` – Kogge-Stone parallel prefix adder
- `BrentKung` – Brent-Kung parallel prefix adder
- `Sklansky` – Sklansky parallel prefix adder
- `SkewAwarePrefix` – greedy prefix adder that minimizes arrival-skewed critical delay using provided per-bit `input_delays` (number applies uniformly, array must match width)

Pipelining is not yet implemented; `pipeline_depth` must be `1`.

## Multiplier Configuration

Multiplier entries support all of the fields from the legacy `multiplier` object: `module_name`, `ppg_algorithm`, `compressor_structure`, `cpa_structure`, and `pipeline_depth`. When using the `operations` array, set `"type": "multiplier"`, reference the operand supplying both inputs, and place the implementation options inside an `options` object.

Currently, `compressor_structure` and `pipeline_depth` are fixed to `AdderTree` and `1`. The `AdderTree` is optimized using ILP as described in [UFO-MAC: A Unified Framework for Optimization of High-Performance Multipliers and Multiply-Accumulators](https://arxiv.org/abs/2408.06935). See [Compressor Tree Memo](doc/compressor_tree/memo_about_compressor_tree.md) for details.

Supported partial product generators (`ppg_algorithm`):

- `Normal`
- `Booth4`

For sign extension a fast computation technique is used, as described in ["Minimizing Energy Dissipation in High-Speed Multipliers"](https://ieeexplore.ieee.org/document/621285). The `bit_width` should be at least 4.

## Multiplier Configuration for Yosys

Yosys-aware multipliers can be emitted either with the legacy `"multiplier_yosys"` object or via an `operations` entry with `"type": "multiplier_yosys"`.

```json
{
    "type": "multiplier_yosys",
    "module_name": "yosys_multiplier16s",
    "operand": "sample",
    "options": {
        "booth_type": "Booth"
    }
}
```

Set `booth_type` to `"Booth"` or `"LowpowerBooth"`. `"LowpowerBooth"` is only valid for signed operands.

## MCM Configuration

Multiple-constant multiplication (MCM) entries describe the constants that must be realized using shift-add graphs built by the algorithms in `mcm_cli`. Each entry uses `"type": "mcm"` and accepts the following fields:

- `operand`: name of the operand definition to use. Defaults to the legacy `operand` if omitted. The shared input name inside the generated RTL automatically reuses this operand name, and individual lanes become `<operand>_<index>` whenever `dimensions > 1`.
- `constants`: array of positive integers. You no longer need to name each constant or specify `post_shift`/`output_width`; the generator derives the result width from the operand width and the magnitude of the largest constant.
- `synthesis`: describes how the shift-add network is produced.
  - `engine`: `"heuristic"` (default) or `"ilp"`.
  - `algorithm`: for heuristics choose from `BHA`, `BHM`, `RAGn`, or `HCub`. For ILP use `GarciaVolkova`.
  - `max_adders`: optional guardrail for ILP runs.
  - `emit_schedule`: when true, the serialized A-operations are written next to the generated Verilog.

See `examples/config_mcm_fir.json` for a compact FIR example that emits three taps using the `HCub` heuristic. Background on the algorithms (BHA, BHM, RAG-n, H_cub, ILP) is in `doc/constant_multiplication.md`.
Generated ports follow the convention `<operand>_0` for the shared input (scalar operands) and `<module_name>_out<i>` for the `i`-th constant.

## CMVM Configuration

Constant matrix-vector multiplication (CMVM) entries use `"type": "cmvm"` and extend the idea to multiple inputs and outputs (e.g., DCT kernels). Required fields:

- `operand`: name of the operand definition that feeds the matrix. Set `dimensions` on that operand equal to the vector length so the generator can construct the lane names `<operand>_0`, `<operand>_1`, … automatically.
- `matrix`: 2-D array written row-major. Each row corresponds to one output channel; each column corresponds to one input lane derived from the operand. Negative coefficients are allowed.
- `synthesis`: selects one of the CMVM algorithms implemented in `cmvm_cli`.
  - `algorithm`: `"ExactILP"`, `"H2MC"`, or `"HCMVM"`.
  - `difference_rows`: when true, pre-process rows with the numerical-difference method before running the heuristic.
  - `max_pair_search`: limit for the number of candidate subexpressions checked per iteration.
  - `fallback_algorithm`: optional algorithm name (`"ExactILP"` or `"H2MC"`) to try on small residuals when the primary algorithm stalls.

Refer to `examples/config_cmvm_dct.json` for a CMVM configuration that builds a 4x4 DCT-like block using the recommended `HCMVM` stage plus a fallback to the exact ILP model on small sub-problems.
Input lanes appear as `<operand>_<column>` and each row emits `module_name_out<i>` with a width derived from the per-row coefficient magnitudes.

## Floating-Point Operations

Floating-point operands use `kind: "fp"` with an accompanying `fp_format` describing the total width and mantissa width (exponent width is derived). Example operand:

```json
{
  "name": "fp32",
  "dimensions": 1,
  "bit_width": 32,
  "signed": true,
  "kind": "fp",
  "fp_format": { "total_width": 32, "mantissa_width": 23 }
}
```

Supported FP operations (each references an `operand` of kind `fp`):

- `fp_mul`: generates a FloPoCo floating-point multiplier and converts it to Verilog through Yosys+GHDL.
  - `module_name`: top module/entity name to emit.
  - `rounding_mode` (optional): placeholder for future extension (default `"RNE"`).
  - `flush_subnormals` (optional): placeholder, default `false`.
  - `pipeline_stages` (optional): placeholder, default `0`.
  - Minimal example:
    ```json
    {
      "type": "fp_mul",
      "module_name": "fp32_mul",
      "operand": "fp32"
    }
    ```

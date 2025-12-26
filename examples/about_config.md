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

## Configuration Space & Search Guidance

RTLGen’s current configuration space (for integer arithmetic) is driven by:
- Operand width, signedness, and `kind` (int vs fp).
- PPG choice (`Normal`, `Booth4`) for multipliers.
- CPA choice (`Ripple`, `BrentKung`, `KoggeStone`, `Sklansky`, `SkewAwarePrefix`) for adders and multipliers.
- Yosys booth mode (`Booth`, `LowpowerBooth`) for `multiplier_yosys` (signed-only for LowpowerBooth).

Evaluation agents should use this space to propose new targets beyond existing
campaigns by scanning for missing combinations across widths, PDKs, and CPA/PPG
options. Use `runs/index.csv` to avoid duplicates.

See `doc/evaluation_agent_guidance.md` for how to triage unexpected PPA results,
how to decide between OpenROAD retuning vs design warnings, and how to record
findings for algorithm developers.

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
- `fp_add`: generates a FloPoCo floating-point adder and converts it to Verilog through Yosys+GHDL. Options mirror `fp_mul`.
  - `module_name`: top module/entity name to emit.
  - `rounding_mode` (optional): placeholder for future extension (default `"RNE"`).
  - `flush_subnormals` (optional): placeholder, default `false`.
  - `pipeline_stages` (optional): placeholder, default `0`.
  - Minimal example:
    ```json
    {
      "type": "fp_add",
      "module_name": "fp32_add",
      "operand": "fp32"
    }
    ```
- `fp_mac`: generates a fused multiply-add (`A*B+C`) using FloPoCo’s `IEEEFPFMA` (IEEE-style 32-bit interface: sign/exponent/fraction, no exception prefix). Ports include `negateAB`, `negateC`, and `RndMode` (2-bit) inputs; defaults are negate off and `RndMode=00` (nearest-even) in tests.
Inputs/outputs follow FloPoCo’s 2-bit exception prefix (`[33:32]` for 32-bit formats): `01` normal, `00` zero/subnormal, `10` infinity, `11` NaN. The remaining bits carry IEEE-like sign/exponent/fraction.

## Activation Functions

Activation entries use `"type": "activation"` with a `function` selector inside `options`:

- `function`: `"relu"`, `"relu6"`, `"leaky_relu"`, or generic `"pwl"` (piecewise-linear) for custom nonlinearities. FP path supports relu and leaky_relu; FP PWL is a coarse staircase (FP32 only) and not recommended for accuracy-sensitive use yet.
- `module_name`: output module name.
- `operand`: operand name to determine width/kind.
- `alpha_num`, `alpha_den` (optional, leaky_relu): scale negative inputs by `alpha_num/alpha_den`. FP leaky_relu currently only supports `alpha_num=1` and `alpha_den` as a power-of-two (implemented as exponent shift).
- `points` (PWL): array of `[x, y]` pairs defining the positive-side curve; negative side mirrors when `symmetric` is true.
- `symmetric` (PWL): when true (default), mirror the points for negative inputs with `f(-x) = -f(x)`.
- `frac_bits` (int PWL): fixed-point scaling for integer operands.
- `clamp` (bool, default true): clamp beyond the last point to the last `y` (mirrored if symmetric).

Behavior:
- Integer operands: two’s-complement inputs; ReLU outputs `0` for negative, input otherwise. ReLU6 clamps to `6` (truncated to width) after ReLU. Leaky_ReLU scales negatives; PWL builds a symmetric piecewise-linear response from the supplied points.
- Floating-point operands (FloPoCo format with 2-bit exception prefix): ReLU zeros negative normal numbers while preserving exn bits (`01` with zero payload); zeros with non-negative sign stay zero; NaN/inf pass through unchanged. Leaky ReLU scales negative normals by shifting the exponent (power-of-two alpha). FP PWL is a coarse FP32-only staircase using user points; for accurate FP behavior prefer relu/leaky.

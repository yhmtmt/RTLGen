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

See `notes/evaluation_agent_guidance.md` for how to triage unexpected PPA results,
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

Multiplier entries support all of the fields from the legacy `multiplier` object: `module_name`, `ppg_algorithm`, `compressor_structure`, `compressor_library`, `compressor_assignment`, `cpa_structure`, and `pipeline_depth`. When using the `operations` array, set `"type": "multiplier"`, reference the operand supplying both inputs, and place the implementation options inside an `options` object.

Currently, `compressor_structure` and `pipeline_depth` are fixed to `AdderTree` and `1`. The `AdderTree` is optimized using ILP as described in [UFO-MAC: A Unified Framework for Optimization of High-Performance Multipliers and Multiply-Accumulators](https://arxiv.org/abs/2408.06935). The `compressor_library` option selects which compressor cells can be used during ILP assignment:
- `fa_ha` (default): 3:2 and 2:2 only
- `fa_ha_c42`: 3:2, 2:2, and 4:2
See [Compressor Tree Memo](../notes/compressor_tree/memo_about_compressor_tree.md) for details.

The `compressor_assignment` option selects the ILP formulation:
- `legacy_fa_ha` (default): prior FA/HA-count-based ILP (3:2/2:2 only).
- `direct_ilp`: direct compressor assignment ILP (supports `fa_ha_c42`).
Note: the current direct ILP solver fails to find solutions for 16-bit and wider multipliers; use `legacy_fa_ha` for practical widths until the solver is fixed. See [Compressor Tree Memo](../notes/compressor_tree/memo_about_compressor_tree.md) for evaluation notes.

Supported partial product generators (`ppg_algorithm`):

- `Normal`
- `Booth4`

For sign extension a fast computation technique is used, as described in ["Minimizing Energy Dissipation in High-Speed Multipliers"](https://ieeexplore.ieee.org/document/621285). The `bit_width` should be at least 4.

## MAC Configuration (Integer, PP-Row Feedback)

MAC entries reuse the multiplier configuration knobs and add one accumulation mode:

- `type`: `"mac"`
- `module_name`: output Verilog module name
- `operand`: operand name used for `multiplicand` and `multiplier`
- `options`: same keys as `multiplier` (`ppg_algorithm`, `compressor_structure`, `compressor_library`, `compressor_assignment`, `cpa_structure`, `pipeline_depth`)
- `accumulation_mode`: currently only `"pp_row_feedback"`

`pp_row_feedback` injects the accumulator input as an additional partial-product row before compressor-tree optimization, so the generated module computes:

`result = multiplicand * multiplier + accumulator`

Current limitation: `accumulator` width is fixed to the full product width (`2 * operand.bit_width`) in this phase.

Example:

```json
{
  "type": "mac",
  "module_name": "int8_mac_pp_feedback",
  "operand": "int8",
  "options": {
    "ppg_algorithm": "Booth4",
    "compressor_structure": "AdderTree",
    "compressor_library": "fa_ha",
    "compressor_assignment": "legacy_fa_ha",
    "cpa_structure": "BrentKung",
    "accumulation_mode": "pp_row_feedback",
    "pipeline_depth": 1
  }
}
```

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

See `examples/config_mcm_fir.json` for a compact FIR example that emits three taps using the `HCub` heuristic. Background on the algorithms (BHA, BHM, RAG-n, H_cub, ILP) is in `notes/constant_multiplication.md`.
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

- `fp_mul`: generates a FloPoCo `FPMult` operator and converts it to Verilog through Yosys+GHDL.
  - `module_name`: top module/entity name to emit.
  - `rounding_mode` (optional): placeholder for future extension (default `"RNE"`; currently not wired to FloPoCo CLI).
  - `flush_subnormals` (optional): placeholder, default `false` (currently metadata only).
  - `pipeline_stages` (optional): placeholder, default `0` (currently metadata only).
  - Interface format: FloPoCo FP encoding (`W = total_width + 2`), with 2-bit exception prefix.
  - Minimal example:
    ```json
    {
      "type": "fp_mul",
      "module_name": "fp32_mul",
      "operand": "fp32"
    }
    ```
- `fp_add`: generates a FloPoCo `FPAdd` operator and converts it to Verilog through Yosys+GHDL. Options mirror `fp_mul`.
  - `module_name`: top module/entity name to emit.
  - Interface format: FloPoCo FP encoding (`W = total_width + 2`), with 2-bit exception prefix.
  - Minimal example:
    ```json
    {
      "type": "fp_add",
      "module_name": "fp32_add",
      "operand": "fp32"
    }
    ```
- `fp_mac`: generates a fused multiply-add (`A*B+C`) using FloPoCo `IEEEFPFMA`.
  - `module_name`: top module/entity name to emit.
  - Interface format: IEEE sign/exponent/fraction only (`W = total_width`, no FloPoCo exception prefix).
  - Extra control inputs: `negateAB`, `negateC`, and `RndMode` (2-bit; tests currently drive `00`, nearest-even).

Compliance status and caveats:

- `fp_mul` (`FPMult`) and `fp_add` (`FPAdd`) are FloPoCo-format operators (`exn[1:0] + sign + exp + frac`), not raw IEEE bit-layout interfaces.
- `fp_mul`/`fp_add` are intended to be correctly-rounded floating-point datapaths in FloPoCo format, but this flow does not currently claim strict IEEE-754 bit-for-bit compliance across all corner cases.
- `fp_mac` uses IEEE-layout ports via `IEEEFPFMA`, but FloPoCo source still contains open TODOs for full IEEE corner-case behavior (for example NaN propagation details and non-RN rounding modes).
- For RTLGen wrappers, `rounding_mode`, `flush_subnormals`, and `pipeline_stages` in JSON are currently placeholders unless explicitly wired in generator code.

Encoding reference:

- FloPoCo FP encoding (`fp_mul`, `fp_add`): `[W-1:W-2]=exn`, then sign/exponent/fraction.
  - `01`: normal
  - `00`: zero/subnormal class
  - `10`: infinity
  - `11`: NaN
- IEEE encoding (`fp_mac`): standard sign/exponent/fraction layout with width `W = total_width`.

## Activation Functions

Activation modules can be generated as **standalone units**, not only through
`npu/rtlgen/gen.py`. This is the recommended path for lower-level optimizer
agents that sweep function approximations and run unit PPA/timing evaluation.

Each activation unit is an `operations[]` entry with:

- `type`: `"activation"`
- `module_name`: generated Verilog module name
- `operand`: operand reference
- `options`: activation options (below)

Generated interface is always scalar and width-matched to the operand:

- `input  [W-1:0] X`
- `output [W-1:0] Y`

Where:

- integer operand: `W = bit_width`
- fp operand: `W = total_width + 2` (FloPoCo-style `exn[1:0]` prefix)

Supported `options.function` values:

- `"relu"`
- `"relu6"` (integer path; FP currently behaves as ReLU)
- `"leaky_relu"`
- `"tanh"`
- `"gelu"`
- `"softmax"` (approximate scalar form)
- `"layernorm"` (scalar placeholder form)
- `"drelu"`
- `"dgelu"`
- `"dsoftmax"`
- `"dlayernorm"`
- `"pwl"` (piecewise linear)

Activation options for optimization flows:

- `function` (required): choose kernel/approximation family.
- `impl` (optional, default `"default"`): implementation hint for future backend selection. Currently metadata only.
- `alpha_num`, `alpha_den` (optional): leaky-ReLU slope ratio (`alpha_num/alpha_den`).
  - FP restriction: `alpha_num=1` and `alpha_den` must be a power of two.
- `frac_bits` (optional): fixed-point scaling for integer PWL.
- `segments` (optional): reserved for future segmentation-based emitters.
- `points` (optional): array of `[x, y]` samples for PWL (recommended path).
- `breakpoints`, `slopes` (optional): alternate integer PWL description.
- `intercepts` (optional): parsed but currently reserved in emitter.
- `clamp` (optional, default `true`): integer PWL out-of-range clamp behavior.
- `symmetric` (optional, default `true`): odd-symmetry mirror for PWL.

Current approximation behavior summary:

- Integer path: deterministic two's-complement approximations for `relu/relu6/leaky_relu/tanh/gelu/softmax/layernorm` and derivative variants.
- FP path: deterministic FloPoCo-encoded approximations for `relu/leaky_relu/tanh/gelu/softmax/layernorm` and derivative variants.
- `pwl`: customizable; integer path uses fixed-point line segments, FP path currently emits a coarse staircase (FP32-only).

Unit-level optimization sweep knobs (typical):

- operand format (`bit_width`, `signed`, `kind`, `fp_format`)
- function family (`function`)
- approximation strength knobs (`alpha_*`, `frac_bits`, number of PWL points)
- shape specification (`points` or `breakpoints/slopes`)
- symmetry/clamping policies (`symmetric`, `clamp`)

Example standalone activation unit:

```json
{
  "type": "activation",
  "module_name": "softmax_int8_u0",
  "operand": "din",
  "options": {
    "function": "softmax"
  }
}
```

## Vector-Op Approximation Notes (NPU Phase-2)

This section documents how `vec_op` math is currently approximated.

- NPU `vec_op` execution in `npu/rtlgen/gen.py` is currently **int8 lane-wise**.
- C++ activation modules in `src/rtlgen/rtl_operations.cpp` support both **int** and **fp** functions; NPU currently imports the int8 variants when `compute.vec.activation_source=rtlgen_cpp`.

### Integer approximation (current NPU vec path)

For each lane value `x` (and optional `y`) in signed int8:

- `add`: `x + y` (8-bit lane result, wraps on overflow)
- `mul`: `x * y` (8-bit lane result, wraps on overflow)
- `relu`: `max(x, 0)`
- `gelu`: `max(x, 0) >> 1`
- `softmax`: `p = 0` if `x < 0`, `p = 127` if `x > 31`, else `p = x << 2`
- `layernorm`: `x >>> 1` (arithmetic right shift by 1)
- `drelu`: `1` if `x > 0`, else `0`
- `dgelu`: `1` if `x > 0`, else `0`
- `dsoftmax`: `(p * (127 - p)) >> 7`, where `p` is the approximate softmax above
- `dlayernorm`: constant `1`

### Floating-point approximation (C++ activation generator)

For FP operands (`kind: "fp"`), RTLGen uses FloPoCo-style encoding (`exn[1:0] + sign + exp + frac`) and emits:

- `relu`: negative normal values map to +0, others pass through
- `gelu`: approximated as `0.5 * relu(x)` (implemented by exponent shift on positive normals)
- `softmax`: negative normal -> +0, sufficiently large positive normal -> +1.0, otherwise pass-through
- `layernorm`: pass-through (`Y = X`) placeholder
- `drelu`: +1.0 for positive non-zero normals, else +0
- `dgelu`: +0.5 for positive non-zero normals, else +0
- `dsoftmax`: constant +0.25 for normal values, else +0
- `dlayernorm`: constant +1.0

These are intentionally simple, deterministic approximations for bring-up and physical-design exploration, not numerically exact implementations of full ML kernels.

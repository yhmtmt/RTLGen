# Score32 Exact Root Finalizer Contract

Phase C closes the semantic boundary that phase B left open: the radix-2 exact-partial tree now feeds an embodied ready/valid root finalizer that performs the exact `attention_online.finalize_value` division for each 328-bit root beat.

## Interface

- Input beat: `command_id`, `head_id`, `slice`, `last`, shared `exp_sum[32:0]`, and 8 signed `S41` numerators packed into 328 payload bits.
- Output beat: `command_id`, `head_id`, `slice`, `last`, and 8 signed `S40` finalized values packed into 320 payload bits.
- Arithmetic: symmetric rounding of `abs(numerator) * 65535 / exp_sum` with sign restore, no combinational `/`, sequential restoring division only.
- Physical divider lanes: `1/2/4/8`, with ideal standalone service of `456/228/114/57` divide cycles per beat.
- Protocol errors: sticky error on `exp_sum == 0`; metadata/last-semantics errors propagate from the tree and are also surfaced at the wrapper boundary.

## Composition Boundary

- The composed wrapper directly connects tree `root_ready` to finalizer `in_ready`, so root backpressure is real.
- The wrapper still exposes the exact-partial internal tree structure and per-stage/node counters for debug and later macro evaluation.
- Direct wide internal links remain unclosed:
  - leaf/tree partial payload beats are still 328-bit numerator bundles
  - this phase does not close NoC/SRAM placement for those links
  - macro/PPA conclusions remain out of scope

## Capacity Notes

- Exact partial state remains `21252 B` per cluster for `32` heads.
- Theoretical leaf traffic remains `26816 B` per cluster for `32` heads.
- The new finalized root stream is narrower than the partial stream, but the wide internal exact-partial links are still the active implementation boundary.

## Reporting Contract

- Probe output must distinguish theoretical `32`-head service accounting from measured workload.
- Measured composed-tree evidence is authoritative for first output, last output, drain cycles, accepted/output counts, and root output interval.
- Standalone divider-cycle figures are ideal service references only; they are not a claim about full-tree initiation interval under backpressure.

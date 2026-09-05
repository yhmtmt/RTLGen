# Llama7B RMSNorm Banked Storage Contract

The Phase-3 RMSNorm arithmetic and ready/valid behavior remain unchanged. This
contract replaces only the physically infeasible inferred `row_mem` and
`gamma_mem` register arrays.

## Exact mapping

- Logical capacity: 4096 elements, each containing one BF16 row value and one
  BF16 gamma value.
- Stream shape: 256 beats of 16 lanes.
- Physical word: `{gamma[15:0], row[15:0]}` (32 bits).
- Available physical primitive: `fakeram45_64x32`.
- Organization: 16 independent lane banks, each split into four 64-word depth
  shards.
- Inventory: exactly 64 macros; 16 macros are enabled for any accepted beat.
- Address mapping: `beat[7:6]` selects the depth shard and `beat[5:0]` selects
  the row within that macro.

`llama7b_rmsnorm_banked_row_gamma_store` embodies this mapping. It accepts one
complete 16-lane write beat per cycle and one complete 16-lane read request per
cycle. Reads return after the fixed two-cycle latency of the checked FakeRAM
model. Simultaneous read and write requests are illegal and set the sticky
`request_collision` diagnostic; neither operation is performed.

## Integration obligations

The Phase-3 controller must account for the two-cycle read latency in both
`ACCUMULATE_REPLAY` and `EMIT`. It must stop issuing reads when the downstream
pipeline cannot absorb the corresponding response; returned data cannot be
dropped or reordered. Input collection writes each accepted beat exactly once.

Two controller policies are embodied. The conservative policy permits one
outstanding read and measures 1800 no-stall cycles per row. The pipelined policy
uses the three slots of the existing elastic arithmetic pipeline as explicit
response credits; it never allows occupied slots plus in-flight reads to exceed
three and measures 1035 cycles. Both policies retain the same 64 macros.
The three-credit policy is additionally checked with twelve-cycle downstream
stall bursts against an independent cycle model; the store response must never
arrive without a reserved arithmetic-pipeline slot.

Equivalence must retain the existing full-row BF16 result, framing-error replay,
exponent-255 canonicalization, row counters, and output-backpressure checks. A
new comparison must additionally cover all four shard boundaries (beats 63/64,
127/128, and 191/192) and the final beat 255.

## Evidence boundary

The checked FakeRAM LEF/Liberty view makes this a concrete Nangate45 proxy-macro
implementation, not foundry SRAM signoff. Macro area and pin activity must be
reported separately from standard-cell controller cost. A physical result is
eligible for architecture recost only when the generated hierarchy contains
exactly 64 macros and no inferred row/gamma memories or replicated register
arrays.

# Llama7B Attention Abstraction Closure Plan

## Goal

Quantify the remaining abstracted parts in the Llama7B 131k clustered attention
schedule until the selected frontier is backed by measured component costs rather
than free or heuristic assumptions.

## Current Measured Baseline

- Compute-array PPA is measured from the `compute_stability_cmp33` family.
- Local full-value attention tile PPA is measured by
  `l1_decoder_attention_full_value_tile_v1`.
- The latest L2 full-value rerun preserved the frontier at
  `1200 mm2 / nm64_flat / 8 clusters / cluster_tree`, with latency
  `15134.080960 us`.

## Remaining Quantities

1. Softmax weight generation
   - Scope: score max, exponent approximation, sum accumulation, reciprocal
     normalization, and normalized weight output.
   - First measurement: `l1_decoder_attention_softmax_weight_generator_v1`.
   - First L2 consumer: add the selected measured softmax profile as per-cluster
     local overhead and rerun the clustered schedule.

2. SRAM timing and energy
   - Scope: tile-local score/value buffering, KV tile reads, partial-value
     buffering, and result writeback.
   - First measurement: SRAM primitive/profile sweep at the tile-buffer widths
     used by the selected frontier.
   - First L2 consumer: replace ideal local/shared SRAM access latency and
     energy with measured bandwidth, access-time, and capacity profiles.

3. NoC arbitration and contention
   - Scope: per-cluster local router/fifo cost is already measured, but current
     schedule still uses bandwidth divided by hop count for contention.
   - First measurement: routed multi-source arbitration microbenchmarks for the
     selected 128-bit and 256-bit local paths.
   - First L2 consumer: replace the bandwidth/hop proxy with measured effective
     payload/cycle and arbitration latency under producer/reducer traffic mixes.

4. Integrated schedule closure
   - Scope: rerun the Llama7B attention schedule with measured compute,
     full-value tile, softmax, SRAM, and NoC profiles.
   - Result: publish a remaining-abstractions table. Any surviving abstraction
     must be explicitly named with a bounded sensitivity parameter.

## Ordering

Run the softmax measurement first because it is the nearest missing compute
block and can be folded into the existing measured-L1 cost file. Then quantify
SRAM before NoC, because the NoC traffic model depends on which buffers are
local, shared, or spilled.

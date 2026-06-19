# Llama7B Attention Abstraction Closure Plan

## Goal

Quantify the remaining abstracted parts in the Llama7B 131k clustered attention
schedule until the selected frontier is backed by measured component costs rather
than free or heuristic assumptions.

## Current Measured Baseline

- Compute-array PPA is measured from the `compute_stability_cmp33` family.
- Local full-value attention tile PPA is measured by
  `l1_decoder_attention_full_value_tile_v1`.
- Tile-local SRAM profile evidence has been merged by
  `prop_l2_decoder_attention_sram_profile_v1` / PR #735.
- NoC traffic profile evidence has been merged by
  `prop_l2_decoder_attention_noc_profile_v1` / PR #736, using the measured
  FIFO/router primitive anchors from `l1_decoder_memory_noc_primitives_v1`.
- The latest L2 full-value rerun preserved the frontier at
  `1200 mm2 / nm64_flat / 8 clusters / cluster_tree`, with latency
  `15134.080960 us`.
- Current active remote-only queue:
  - `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`,
    assigned to `eval-daemon-b7c2d9c80c1c`, source `63df7c30`.
  - `l2_decoder_attention_kv_model_native_quality_7b_v1`, assigned to the same
    remote evaluator, source `63df7c30`.
- `l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1`
  is staged but blocked until the L1 q12/PWL PPA item is merged/materialized.

## Remaining Quantities

1. Composed q12/PWL softmax datapath PPA
   - Scope: score max, exponent approximation, sum accumulation, reciprocal
     normalization, normalized weight output, and value mixing inside the
     composed dual-stream attention wrapper.
   - Active measurement:
     `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`.
   - First L2 consumer:
     `l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1`
     substitutes the measured q12/PWL wrapper into the current Llama7B subtile
     schedule and compares latency, area, energy, and precision-risk posture
     against the reciprocal-LUT composed frontier.

2. Native 7B precision quality
   - Scope: teacher-forced decode on a real 7B-class checkpoint with KV8/KV4
     cache quantization feedback.
   - Active gate: `l2_decoder_attention_kv_model_native_quality_7b_v1`.
   - Result use: keep KV8 as the conservative frontier unless KV4 survives
     top-1/top-k/logit-cosine/KL/margin-sensitive checks, or schedule a
     QAT/scale-granularity recovery job if KV4 fails but still looks valuable.

3. SRAM timing and energy
   - Scope: tile-local score/value buffering, KV tile reads, partial-value
     buffering, and result writeback.
   - Status: measured/merged by `l2_decoder_attention_sram_profile_v1`.
   - Remaining work: verify the final integrated schedule consumes the merged
     SRAM profile and reports any surviving SRAM abstraction as an explicit
     sensitivity term, not as an implicit ideal buffer.

4. NoC arbitration and contention
   - Scope: per-cluster local router/fifo cost is already measured, but current
     schedule still uses bandwidth divided by hop count for contention.
   - Status: measured/merged by `l2_decoder_attention_noc_profile_v1`.
   - Remaining work: verify the final integrated schedule consumes explicit
     payload/cycle and arbitration-latency bounds under the selected
     producer/reducer traffic mix.

5. Integrated schedule closure
   - Scope: rerun the Llama7B attention schedule with measured compute,
     full-value tile, softmax, SRAM, and NoC profiles.
   - Result: publish a remaining-abstractions table. Any surviving abstraction
     must be explicitly named with a bounded sensitivity parameter.

## Ordering

Keep the remote evaluator focused on the L1 q12/PWL composed softmax PPA first;
it is the dependency that unblocks the staged q12/PWL Llama7B frontier
substitution. Run the native 7B precision gate in parallel only when the remote
evaluator has capacity, because it is evidence-only and has no OpenROAD/PPA
step. After both results are merged, rerun the integrated closure and publish
the remaining-abstractions table.

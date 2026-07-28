# attention_score32_exact_local_temporal_reducer_gqa8_physical_harness

This harness is a narrow-IO structural PPA wrapper around
`gen_attention_score32_exact_local_temporal_reducer_gqa8.py`.

- Inputs are fixed to `clk`, `rst_n`, `start`, and `seed`.
- Observable outputs are fixed to `done`, final command/head/max/sum/slice/last/value state, `source_fold`, and the harness counters.
- `producers` is fixed to `53` or `54`.
- `mode` is fixed to `reducer` or `source_only`.
- `waves` is fixed to `8`.
- The source schedule is fixed to `2` explicit GQA8 command groups with head bases `[0, 8]`, `8` heads per group, `16` slices per head, and `8` waves per command group.
- Leaf traffic is generated from one shared held LFSR and one shared `12`-bit batch counter. Leaf-specific exact-partial fields are combinational and there are no per-leaf payload registers.
- All leaf valids form one atomic batch. Shared state advances only when every leaf handshakes, so every payload remains stable throughout reducer backpressure.
- Source ordering is head-major and slice-minor within each wave. Wave advance happens only after the terminal source beat `head lane 7, slice 15, last=1`.
- `reducer` mode instantiates the corrected GQA8 local temporal reducer unchanged.
- Both modes retain the same full source fold. `source_only` accepts each batch atomically and exposes the direct source command/head/max/sum/slice/last/value projection through the final observable outputs so the source fabric is not optimized away.
- The manifest must carry the caveats `structural_only` and `nonlinear_ppa_delta_vs_functional_reducer_measurement`.
- The harness reports actual external top pins only and must not be used as a functional replacement for the structured GQA8 reducer probe.
